'use strict';

(function() {
    angular.module('fireStation.heatmapService', [])
        .factory('heatmap', HeatmapService)
    ;

    HeatmapService.$inject = ['$http', '$q', '$rootScope'];

    function HeatmapService($http, $q, $rootScope) {
        var _map = null;
        var _layer = L.heatLayer([], {
            gradient: {0.55: '#74ac49', 0.65: '#febe00', 1: '#f6542f'},
            radius: 10,
            minOpacity: 0.5
        });
        var _crossfilter = null;
        var _fires = {
            dates: null,
            months: null,
            days: null,
            hours: null
        };
        var _filters = {
            months: [],
            days: [],
            hours: []
        };
        var _totals = {};

        function processData(allText) {
            var allTextLines = allText.split(/\r\n|\n/);
            var headers = allTextLines[0].split(',');
            var lines = [];

            for (var i = 1; i < allTextLines.length; i++) {
                var data = allTextLines[i].split(',');
                if (data.length == headers.length) {

                    var tarr = {};
                    for (var j = 0; j < headers.length; j++) {
                        tarr[headers[j]] = data[j];
                    }

                    lines.push(tarr);
                }
            }
            return lines
        }

        return {
            get layer()     { return _layer; },
            get filters()   { return _filters; },
            get totals()    { return _totals; },

            init: function(map) {
                _map = map;
            },

            onRefresh: function(scope, callback) {
                var handler = $rootScope.$on('heatmap.onRefresh', callback);
				scope.$on('$destroy', handler);
            },

            reset: function() {
                for (var i = 0; i < _filters.length; i++) {
                    this.resetFilter(_filters[i]);
                }
            },

            resetFilter: function(filterType) {
                this.setFilter(filterType, []);
            },

            setFilter: function(filterType, indices) {
                _filters[filterType] = indices || [];

                var filter = _filters[filterType];
                if (filter.length) {
                    _fires[filterType].filter(function(d) {
                        return (filter.indexOf(d) > -1);
                    });
                } else {
                    _fires[filterType].filterAll();
                }

                this.refresh();
            },

            addToFilter: function(filterType, additions) {
                // Allow single values to be passed in, as well as arrays.
                if (!Array.isArray(additions)) {
                    additions = [additions];
                }

                var filter = _filters[filterType];
                for (var i = 0; i < additions.length; i++) {
                    if (filter.indexOf(additions[i]) === -1) {
                        filter.push(additions[i]);
                    }
                }

                this.setFilter(filterType, filter);
            },

            removeFromFilter: function(filterType, removals) {
                // Allow single values to be passed in, as well as arrays.
                if (!Array.isArray(removals)) {
                    removals = [removals];
                }

                var filter = _filters[filterType];
                for (var i = 0; i < removals.length; i++) {
                    var index = filter.indexOf(removals[i]);
                    if (index > -1) {
                        filter.splice(index, 1);
                    }
                }

                this.setFilter(filterType, filter);
            },

            refresh: function() {
                // Update layer with new fire points.
                _layer.setLatLngs(_fires.dates.top(Infinity).map(function(fire) {
                    return [fire.y, fire.x];
                }));

                // Notify listeners.
                $rootScope.$emit('heatmap.onRefresh');
            },

            download: function(url) {
                var self = this;
                return $q(function(resolve, reject) {
                    $http.get(url)
                        .then(function(response) {
                            var lines = processData(response.data);
                            _crossfilter = crossfilter(lines);

                            _fires.dates = _crossfilter.dimension(function(d) { return new Date(d.alarm); });
                            _fires.months = _crossfilter.dimension(function(d) { return new Date(d.alarm).getMonth(); });
                            _fires.days = _crossfilter.dimension(function(d) { return new Date(d.alarm).getDay(); });
                            _fires.hours = _crossfilter.dimension(function(d) { return new Date(d.alarm).getHours(); });

                            _totals.months = _fires.months.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.days = _fires.days.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.hours = _fires.hours.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });

                            self.refresh();

                            resolve();
                        }, function(err) {
                            reject(err);
                        })
                    ;
                });
            }
        }
    }
})();
