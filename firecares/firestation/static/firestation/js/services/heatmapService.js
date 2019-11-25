'use strict';

(function() {
  angular.module('fireStation.heatmapService', [])
    .factory('heatmap', HeatmapService);

  angular.module('fireStation.emsHeatmapService', [])
    .factory('emsHeatmap', HeatmapService);

  HeatmapService.$inject = ['$http', '$q', '$rootScope'];

  function HeatmapService($http, $q, $rootScope) {
    var _map = null;
    var _layer = null;
    var _clipLayer = null;
    var _polygons = null;
    var _crossfilter = null;
    var _fires = {
      dates: null,
      months: null,
      daysOfWeek: null,
      hours: null,
      risk: null
    };
    var _filters = {
      months: [],
      daysOfWeek: [],
      hours: [],
      risk: [],
      yearsMonths: []
    };
    var _totals = {};
    var _labels = {
      months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      daysOfWeek: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      hours: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24'],
      risk: ['Unknown', 'Low', 'Medium', 'High'],
    };
    var _isDownloaded = false;

    function processData(allText) {
      var risks = { 'Unknown':0, 'Low':1, 'Medium':2, 'High':3 };
      var allTextLines = allText.split(/\r\n|\n/);
      var headers = allTextLines[0].split(',');
      var lines = [];

      for (var i = 0; i < allTextLines.length; i += 1) {
        var data = allTextLines[i].split(',');
        if (data.length !== headers.length) {
          continue;
        }

        var tarr = {};
        for (var j = 0; j < headers.length; j += 1) {
          tarr[headers[j]] = data[j];
        }

        tarr.x = parseFloat(tarr.x);
        tarr.y = parseFloat(tarr.y);

        if (isNaN(tarr.x) || isNaN(tarr.y)) {
          continue;
        }

        var dateTime = tarr.alarm.split(' ');
        var yearMonthDay = dateTime[0].split('-');
        var hoursMinutesSeconds = dateTime[1].split(':');

        var year = Number(yearMonthDay[0]);
        var month = Number(yearMonthDay[1]);
        var day = Number(yearMonthDay[2]);
        var risk = risks[tarr.risk_category];

        tarr.dateTime = {
          year: year,
          month: month - 1,
          dayOfWeek: dayOfWeek(year, month, day),
          hours: Number(hoursMinutesSeconds[0]),
          risk: risk
        };

        lines.push(tarr);
      }

      return lines
    }

    // Manually calculate day of week to avoid slow Date parsing.
    // https://en.wikipedia.org/wiki/Determination_of_the_day_of_the_week#Implementation-dependent_methods
    function dayOfWeek(y, m, d) {
      var t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4];
      y -= m < 3;
      return (y + Math.floor(y/4) - Math.floor(y/100) + Math.floor(y/400) + t[m-1] + d) % 7;
    }

    function isFireInPolygons(fire) {
      var polygonIndex = -1;
      for (var i = 0; i < _polygons.length; i += 1) {
        var polyData = _polygons[i];
        var bounds = polyData.bounds;

        if (!(fire.y < bounds[0][0] || fire.y > bounds[1][0] || fire.x < bounds[0][1] || fire.x > bounds[1][1])) {
          polygonIndex = i;
        }
      }

      if (polygonIndex === -1) {
        // Not in any polygon's bounds.
        return false;
      }

      // Use ray-casting algorithm to check if the fire is in the polygon.
      var verts = _polygons[polygonIndex].verts;
      var inside = false;
      for (var i = 0, j = verts.length - 1; i < verts.length; j = i, i += 1) {
        if (((verts[i][0] > fire.x) !== (verts[j][0] > fire.x)) && (fire.y < (verts[j][1] - verts[i][1]) * (fire.x - verts[i][0]) / (verts[j][0] - verts[i][0]) + verts[i][1])) {
          inside = !inside;
        }
      }

      return inside;
    }

    function polygonBounds(coords) {
      var xMin = Number.POSITIVE_INFINITY;
      var yMin = Number.POSITIVE_INFINITY;
      var xMax = Number.NEGATIVE_INFINITY;
      var yMax = Number.NEGATIVE_INFINITY;

      for (var i = 0; i < coords.length; i += 1) {
        var x = coords[i][1];
        var y = coords[i][0];

        xMin = Math.min(xMin, x);
        yMin = Math.min(yMin, y);
        xMax = Math.max(xMax, x);
        yMax = Math.max(yMax, y);
      }

      return [ [xMin, yMin], [xMax, yMax] ];
    }

    return {
      get layer()         { return _layer; },
      get filters()       { return _filters; },
      get totals()        { return _totals; },
      get labels()        { return _labels; },
      get isDownloaded()  { return _isDownloaded; },

      init: function(map, layerOptions) {
        layerOptions = layerOptions || {};
        layerOptions.gradient = layerOptions.gradient || { 0.55: '#74ac49', 0.65: '#febe00', 1: '#f6542f' };
        layerOptions.radius = layerOptions.radius || 10;
        layerOptions.minOpacity = layerOptions.minOpacity || 0.5;
        layerOptions.maxZoom = layerOptions.maxZoom || 15;

        _map = map;
        _layer = L.heatLayer([], layerOptions);
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
        for (var i = 0; i < _filters.length; i += 1) {
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
        _map.fireEvent( 'heatmapfilterchanged',  {
          filterType: filterType,
          filter: filter
        });
        this.refresh();
      },

      setClipLayer: function(clipLayer) {
        _clipLayer = clipLayer;
        _polygons = [];
        _clipLayer.eachLayer(function (layer) {
          if (!layer.feature
            || !layer.feature.geometry
            || !layer.feature.geometry.type
            || ['Polygon', 'MultiPolygon'].indexOf(layer.feature.geometry.type) === -1) {
            return;
          }

          var geometry = layer.toGeoJSON().geometry;
          var polygonsData = (geometry.type === 'Polygon') ? [geometry.coordinates] : geometry.coordinates;

          polygonsData.forEach(function(coordsArray) {
            var verts = [[0, 0]];

            for (var i = 0; i < coordsArray.length; i += 1) {
              var coords = coordsArray[i];

              for (var j = 0; j < coords.length; j += 1) {
                verts.push(coords[j]);
              }

              verts.push(coords[0]);
              verts.push([0, 0]);
            }

            _polygons.push({
              verts: verts,
              bounds: polygonBounds(coordsArray[0]),
            });
          });
        });
      },

      add: function(filterType, keys) {
        // Allow single values to be passed in, as well as arrays.
        if (!Array.isArray(keys)) {
          keys = [keys];
        }

        var filter = _filters[filterType];
        for (var i = 0; i < keys.length; i += 1) {
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
        for (var i = 0; i < keys.length; i += 1) {
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
        var latLngs = _fires.dates.top(Infinity).map(function(fire) {
          return [fire.y, fire.x];
        });

        _layer.setLatLngs(latLngs);

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
              _isDownloaded = true;

              var fires = processData(response.data);
              if (fires.length === 0) {
                reject(new Error('Heatmap data is not yet available for this department.'));
                return;
              }

              if (_polygons) {
                fires = fires.filter(isFireInPolygons);
              }

              _crossfilter = crossfilter(fires);
              _fires.dates = _crossfilter.dimension(function(d) { return d.alarm; });
              _fires.months = _crossfilter.dimension(function(d) { return d.dateTime.month; });
              _fires.daysOfWeek = _crossfilter.dimension(function(d) { return d.dateTime.dayOfWeek; });
              _fires.hours = _crossfilter.dimension(function(d) { return d.dateTime.hours; });
              _fires.yearsMonths = _crossfilter.dimension(function(d) {
                return self.keyForYearsMonths(d.dateTime.year, d.dateTime.month);});
              _fires.risk = _crossfilter.dimension(function(d) { return d.dateTime.risk; });
              _totals.months = _fires.months.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
              _totals.daysOfWeek = _fires.daysOfWeek.group().top(Infinity).sort(function(a, b) { return a.key - b.key;});
              _totals.hours = _fires.hours.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });
              _totals.yearsMonths = _fires.yearsMonths.group().top(Infinity).sort(function(a, b) {
                return a.key.localeCompare(b.key);
              });
              _totals.risk = _fires.risk.group().top(Infinity).sort(function(a, b) { return a.key - b.key; });

              self.refresh();

              resolve();
            }, function(err) {
              reject(err);
            });
        });
      },
    }
  }
})();
