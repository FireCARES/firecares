'use strict';

(function() {
  angular.module('fireStation.emsHeatmapService', [])
    .factory('emsHeatmap', emsHeatmapService);

  emsHeatmapService.$inject = ['$http', '$q', '$rootScope'];

  function emsHeatmapService($http, $q, $rootScope) {
    return {
      get layer() {
        return _layer;
      },
      get filters() {
        return _filters;
      },
      get totals() {
        return _totals;
      },
      get labels() {
        return _labels;
      },

      init: function(map) {
        _map = map;
      },

      onRefresh: function(scope, callback) {
        var handler = $rootScope.$on('emsHeatmap.onRefresh', callback);
        scope.$on('$destroy', handler);
      },

      onFilterChanged: function(filterType, scope, callback) {
        var handler = $rootScope.$on('emsHeatmap.' + filterType + 'FilterChanged', callback);
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

      setFilter: function(filterType, keys) {
        _filters[filterType] = keys || [];

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
        _map.fireEvent('heatmapfilterchanged', {
          filterType: filterType,
          filter: filter
        });
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
        _layer.setLatLngs(_fires.dates.top(Infinity).filter(function(fire) {
          return (fire.y !== "" && fire.x !== "");
        }).map(function(fire) {
          return [fire.y, fire.x];
        }));

        // Notify listeners.
        $rootScope.$emit('heatmap.onRefresh');
      },

      keyForYearsMonths: function(year, month) {
        month = '' + (month + 1);
        var pad = '00';
        month = pad.substring(0, pad.length - month.length) + month;
        return year + '-' + month;
      },

      download: function(url) {
        var self = this;
        return $q(function(resolve, reject) {
          $http.get(url)
            .then(function(response) {
              var lines = processData(response.data);
              if (lines.length == 0) {
                reject(new Error("Heatmap data is not yet available for this department."));
                return;
              }

              // Preprocess dates into individual parts. This is MUCH faster than
              // doing it for each dimension, and speeds up loading significantly.
              var risks = {
                "Unknown": 0,
                "Low": 1,
                "Medium": 2,
                "High": 3
              };
              for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                var dateTime = line.alarm.split(' ');
                var yearMonthDay = dateTime[0].split('-');
                var hoursMinutesSeconds = dateTime[1].split(':');

                var year = Number(yearMonthDay[0]);
                var month = Number(yearMonthDay[1]);
                var day = Number(yearMonthDay[2]);
                var risk = risks[line.risk_category];

                line.dateTime = {
                  year: year,
                  month: month - 1,
                  dayOfWeek: dayOfWeek(year, month, day),
                  hours: Number(hoursMinutesSeconds[0]),
                  risk: risk
                };
              }

              _crossfilter = crossfilter(lines);

              _fires.dates = _crossfilter.dimension(function(d) {
                return d.alarm;
              });
              _fires.months = _crossfilter.dimension(function(d) {
                return d.dateTime.month;
              });
              _fires.daysOfWeek = _crossfilter.dimension(function(d) {
                return d.dateTime.dayOfWeek;
              });
              _fires.hours = _crossfilter.dimension(function(d) {
                return d.dateTime.hours;
              });
              _fires.yearsMonths = _crossfilter.dimension(function(d) {
                return self.keyForYearsMonths(d.dateTime.year, d.dateTime.month);
              });
              _fires.risk = _crossfilter.dimension(function(d) {
                return d.dateTime.risk;
              });

              _totals.months = _fires.months.group().top(Infinity).sort(function(a, b) {
                return a.key - b.key;
              });
              _totals.daysOfWeek = _fires.daysOfWeek.group().top(Infinity).sort(function(a, b) {
                return a.key - b.key;
              });
              _totals.hours = _fires.hours.group().top(Infinity).sort(function(a, b) {
                return a.key - b.key;
              });
              _totals.yearsMonths = _fires.yearsMonths.group().top(Infinity).sort(function(a, b) {
                return a.key.localeCompare(b.key);
              });
              _totals.risk = _fires.risk.group().top(Infinity).sort(function(a, b) {
                return a.key - b.key;
              });

              self.refresh();

              resolve();
            }, function(err) {
              reject(err);
            });
        });
      }
    }
  }
})();
