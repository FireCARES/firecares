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
            hours: [],
            monthsByYear: []
        };
        var _totals = {};
        var _labels = {
            months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            days: ['Sat', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun']
        };

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
            get labels()    { return _labels; },

            init: function(map) {
                _map = map;
            },

            onRefresh: function(scope, callback) {
                var handler = $rootScope.$on('heatmap.onRefresh', callback);
				scope.$on('$destroy', handler);
            },

            onFilterChanged: function(filterType, scope, callback) {
                var handler = $rootScope.$on('heatmap.' + filterType + 'FilterChanged', callback);
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

                // Notify listeners.
                $rootScope.$emit('heatmap.' + filterType + 'FilterChanged', filter);

                this.refresh();
            },

            add: function(filterType, keys) {
                // Allow single values to be passed in, as well as arrays.
                if (!Array.isArray(keys)) {
                    keys = [keys];
                }

                var filter = _filters[filterType];
                for (var i = 0; i < keys.length; i++) {
                    if (filter.indexOf(keys[i]) === -1) {
                        filter.push(keys[i]);
                    }
                }

                this.setFilter(filterType, filter);
            },

            remove: function(filterType, keys) {
                // Allow single values to be passed in, as well as arrays.
                if (!Array.isArray(keys)) {
                    keys = [keys];
                }

                var filter = _filters[filterType];
                for (var i = 0; i < keys.length; i++) {
                    var index = filter.indexOf(keys[i]);
                    if (index > -1) {
                        filter.splice(index, 1);
                    }
                }

                this.setFilter(filterType, filter);
            },

            toggle: function(filterType, key) {
                if (_filters[filterType].indexOf(key) === -1) {
                    this.add(filterType, key)
                } else {
                    this.remove(filterType, key);
                }
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

                            _fires.dates = _crossfilter.dimension(function(d) { return moment(d.alarm, 'YYYY-MM-DD HH:mm:ss').toDate(); });
                            _fires.months = _crossfilter.dimension(function(d) { return moment(d.alarm, 'YYYY-MM-DD HH:mm:ss').month(); });
                            _fires.days = _crossfilter.dimension(function(d) { return moment(d.alarm, 'YYYY-MM-DD HH:mm:ss').day(); });
                            _fires.hours = _crossfilter.dimension(function(d) { return moment(d.alarm, 'YYYY-MM-DD HH:mm:ss').hours(); });
                            _fires.monthsByYear = _crossfilter.dimension(function(d) {
                                var date = moment(d.alarm, 'YYYY-MM-DD HH:mm:ss');
                                var year = date.year();
                                var month = '' + date.month();
                                var pad = '00';
                                month = pad.substring(0, pad.length - month.length) + month;
                                return year + '-' + month;
                            });

                            _totals.months = _fires.months.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.days = _fires.days.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.hours = _fires.hours.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.monthsByYear = _fires.monthsByYear.group().top(Infinity).sort(function(a, b) {
                                return a.key.localeCompare(b.key);
                            });

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
