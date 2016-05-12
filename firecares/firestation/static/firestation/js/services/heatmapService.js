'use strict';

(function() {
    angular.module('fireStation.heatmapService', [])
        .factory('heatmap', HeatmapService)
    ;

    HeatmapService.$inject = ['$http', '$q'];

    function HeatmapService($http, $q) {
        var _map = null;
        var _layer = L.heatLayer([], {gradient: {0.55: '#74ac49', 0.65: '#febe00', 1: '#f6542f'}, radius: 5});
        var _crossfilter = null;
        var _firesByDate = null;
        var _filteredFires = [];
        var _filter = {
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

        function updateLayerOptions() {
            if (!_crossfilter) {
                return;
            }

            var portion = _filteredFires.length / _crossfilter.size();
            var n = (22 - _map.getZoom()) / 22;
            var i = 17 * n * (portion / 2 + .5) + 3;

            _layer.setOptions({
                radius: i,
                blur: 1.3 * (i - 2.99),
                minOpacity: (1 - portion) * (1 - n) * .5
            });
        }

        return {
            get layer()     { return _layer; },
            get filter()    { return _filter; },
            get totals()    { return _totals; },

            init: function(map) {
                _map = map;
                _map.on('zoomend', function() {
                    updateLayerOptions();
                });
            },

            setFilter: function(filterType, indices) {
                if (filterType == 'months') {
                    this.filterMonths(indices);
                } else if (filterType == 'days') {
                    this.filterDays(indices);
                } else if (filterType == 'hours') {
                    this.filterHours(indices);
                } else {
                    console.error("Unsupported filter type '" + filterType + "'");
                }
            },

            filterMonths: function(months) {
                _filter.months = months || [];
                this.refresh();
            },

            filterDays: function(days) {
                _filter.days = days || [];
                this.refresh();
            },

            filterHours: function(hours) {
                _filter.hours = hours || [];
                this.refresh();
            },

            refresh: function() {
                var fires = _firesByDate.filter(function(date) {
                    var month = date.getMonth();
                    var day = date.getDay();
                    var hour = date.getHours();

                    if (_filter.months.length > 0) {
                        if (_filter.months.indexOf(month) == -1) {
                            return false;
                        }
                    }

                    if (_filter.days.length > 0) {
                        if (_filter.days.indexOf(day) == -1) {
                            return false;
                        }
                    }

                    if (_filter.hours.length > 0) {
                        if (_filter.hours.indexOf(hour) == -1) {
                            return false;
                        }
                    }

                    return true;
                });

                _filteredFires = fires.top(Infinity);

                _layer.setLatLngs(_filteredFires.map(function(fire) {
                    return [fire.y, fire.x];
                }));

                updateLayerOptions();
            },

            download: function(url) {
                var self = this;
                return $q(function(resolve, reject) {
                    $http.get(url)
                        .then(function(response) {
                            var lines = processData(response.data);
                            _crossfilter = crossfilter(lines);
                            _firesByDate = _crossfilter.dimension(function(fire) {
                                return new Date(fire.alarm);
                            });

                            // var month0Day2AllHours = firesByDate.filter(function(date) {
                            //     var month = date.getMonth();
                            //     var day = date.getDay();
                            //     return (month == 0 && day == 2);
                            // });

                            ///////////////////////////////////////////
                            var fires = {};
                            fires.hours = _crossfilter.dimension(function(d) { return new Date(d.alarm).getHours(); });
                            fires.days = _crossfilter.dimension(function(d) { return new Date(d.alarm).getDay(); });
                            fires.months = _crossfilter.dimension(function(d) { return new Date(d.alarm).getMonth(); });
                            _totals.hours = fires.hours.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.days = fires.days.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            _totals.months = fires.months.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
                            ///////////////////////////////////////////

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
