'use strict';

(function() {
  angular.module('fireStation.mapFactoryService', [])
    .factory('mapFactory', MapFactoryService)
  ;

  MapFactoryService.$inject = ['$http', '$filter', 'heatmap', 'emsHeatmap'];

  function MapFactoryService($http, $filter, heatmap, emsHeatmap) {
    return {
      create: function(div, options) {
        var defaultOptions = {
          boxZoom: true,
          zoom: 15,
          zoomControl: true,
          attributionControl: false,
          scrollWheelZoom: false,
          doubleClickZoom: false,
          fullscreenControl: false
        };

        angular.extend(defaultOptions, options);
        var map = L.map(div, options);

        // Add base layer.
        var retina = L.Browser.retina ? '@2x': '';

        L.tileLayer('https://{s}.firecares.org/base/{z}/{x}/{y}' + retina + '.png', {
          attribution: '© Mapbox',
          opacity: 0.95,
        }).addTo(map);

        return map;
      },

      addFireHeatmapOverlay: function(args) {
        var requiredArgs = ['map', 'layersControl', 'departmentId'];
        requiredArgs.forEach(function(name) {
          if (!angular.isDefined(args[name])) {
            throw new Error('args.' + name + ' is required!');
          }
        });

        var heatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + args.departmentId + '-building-fires.csv';
        $http.head(heatmapDataUrl)
          .then(function(response) {
            var contentLength = Number(response.headers('Content-Length'));

            // Don't show the heatmap layer option for a department with no heatmap data.
            // HACK: A department with no heatmap data will still return the table header for the empty data, which
            //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
            if (contentLength <= 59) {
              return;
            }

            heatmap.init(args.map);

            args.layersControl.addOverlay(heatmap.layer, 'Fires Heatmap');
            args.map.on('overlayadd', function(layer) {
              if (layer.layer._leaflet_id !== heatmap.layer._leaflet_id) {
                return;
              }

              if (heatmap.isDownloaded) {
                if (args.onShow) {
                  args.onShow(true);
                }
              } else {
                args.map.spin(true);
                heatmap.download(heatmapDataUrl)
                  .then(function() {
                    if (args.onShow) {
                      args.onShow(true);
                    }
                  }, function(err) {
                    args.layersControl.removeLayer(heatmap.layer);
                    if (args.onError) {
                      args.onError(err);
                    }
                  })
                  .finally(function() {
                    args.map.spin(false);
                  })
                ;
              }
            });

            args.map.on('overlayremove', function(layer) {
              if (layer.layer._leaflet_id !== heatmap.layer._leaflet_id) {
                return;
              }

              if (args.onShow) {
                args.onShow(false);
              }
            });

            if (args.onInit) {
              args.onInit(heatmap.layer);
            }
          })
        ;
      },

      addEMSHeatmapOverlay: function(args) {
        var requiredArgs = ['map', 'layersControl', 'departmentId'];
        requiredArgs.forEach(function(name) {
          if (!angular.isDefined(args[name])) {
            throw new Error('args.' + name + ' is required!');
          }
        });

        var emsHeatmapDataUrl = 'https://s3.amazonaws.com/firecares-test/' + args.departmentId + '-ems-incidents.csv';
        $http.head(emsHeatmapDataUrl)
          .then(function(response) {
            var contentLength = Number(response.headers('Content-Length'));

            // Don't show the heatmap layer option for a department with no heatmap data.
            // HACK: A department with no heatmap data will still return the table header for the empty data, which
            //       has a length of 59 bytes. Remember to change this value if the columns ever change in any way.
            if (contentLength <= 59) {
              return;
            }

            emsHeatmap.init(args.map, {
              gradient: { 0.55: '#7400ff', 0.65: '#3333ff', 1: '#ff3333' },
            });

            args.layersControl.addOverlay(emsHeatmap.layer, 'EMS Heatmap');
            args.map.on('overlayadd', function(layer) {
              if (layer.layer._leaflet_id !== emsHeatmap.layer._leaflet_id) {
                return;
              }

              if (emsHeatmap.isDownloaded) {
                if (args.onShow) {
                  args.onShow(true);
                }
              } else {
                args.map.spin(true);
                emsHeatmap.download(emsHeatmapDataUrl)
                  .then(function() {
                    if (args.onShow) {
                      args.onShow(true);
                    }
                  }, function(err) {
                    args.layersControl.removeLayer(emsHeatmap.layer);
                    if (args.onError) {
                      args.onError(err);
                    }
                  })
                  .finally(function() {
                    args.map.spin(false);
                  })
                ;
              }
            });

            args.map.on('overlayremove', function(layer) {
              if (layer.layer._leaflet_id !== emsHeatmap.layer._leaflet_id) {
                return;
              }

              if (args.onShow) {
                args.onShow(false);
              }
            });

            if (args.onInit) {
              args.onInit(emsHeatmap.layer);
            }
          })
        ;
      },

      addParcelsOverlay: function(args) {
        var requiredArgs = ['map', 'layersControl', 'isAuthenticated'];
        requiredArgs.forEach(function(name) {
          if (!angular.isDefined(args[name])) {
            throw new Error('args.' + name + ' is required!');
          }
        });

        var previousParcels = {};

        var parcelsLayer = new L.TileLayer.MVTSource({
          url: 'https://{s}.firecares.org/parcels/{z}/{x}/{y}.pbf',
          debug: false,
          mutexToggle: true,
          maxZoom: 18,
          minZoom: 10,

          getIDForLayerFeature: function(feature) {
            return feature.properties.parcel_id;
          },

          style: function(feature) {
            // Join coordinates.
            var currentCoordinates = '';
            feature.coordinates[0].forEach(function(currentValue) {
              currentCoordinates += currentValue.x + currentValue.y;
            });

            // If overlapping parcel then make it transparent.
            if (currentCoordinates in previousParcels) {
              return {
                color: 'rgba(0,0,0,0)'
              }
            } else {
              previousParcels[currentCoordinates] = null;
            }

            var style = {};

            function scaleDependentPointRadius(zoom) {
              // Set point radius based on zoom
              var pointRadius = 1;
              if (zoom >= 0 && zoom <= 7) {
                pointRadius = 1;
              }
              else if (zoom > 7 && zoom <= 10) {
                pointRadius = 2;
              }
              else if (zoom > 10) {
                pointRadius = 3;
              }

              return pointRadius;
            }

            var type = feature.type;
            switch (type) {
            case 1: //'Point'
              // unselected
              style.color = CICO_LAYERS[feature.properties.type].color || '#3086AB';
              style.radius = scaleDependentPointRadius;
              // selected
              style.selected = {
                color: 'rgba(255,255,0,0.5)',
                radius: 6
              };
              break;
            case 2: //'LineString'
              // unselected
              style.color = 'rgba(161,217,155,0.8)';
              style.size = 3;
              // selected
              style.selected = {
                color: 'rgba(255,255,0,0.5)',
                size: 6
              };
              break;
            case 3: //'Polygon'
              // unselected
              switch (feature.properties.risk_category) {
              case 'Low':
                style.color = 'rgba(50%,100%,50%,0.2)';
                break;
              case 'Medium':
                style.color = 'rgba(100%,75%,50%,0.2)';
                break;
              case 'High':
                style.color = 'rgba(100%,50%,50%,0.2)';
                break;
              default:
                style.color = 'rgba(50%,50%,50%,0.2)';
                break;
              }

              style.outline = {
                color: 'rgb(20,20,20)',
                size: 1
              };
              // selected
              style.selected = {
                color: 'rgba(255,255,0,0.5)',
                outline: {
                  color: '#d9534f',
                  size: 3
                }
              };
            }

            return style;
          },

          onClick: function(evt) {
            if (!args.isAuthenticated) {
              return;
            }

            var message = 'No parcel data found at this location.';
            if (evt.feature != null) {
              message = '';

              var items = {
                'Address': 'addr',
                'City': 'city',
                'State': 'state',
                'Zip': 'zip',
                'Building Sq Footage': 'bld_sq_ft',
                'Stories': 'story_nbr',
                'Units': 'units_nbr',
                'Condition': 'condition',
                'Year Built': 'yr_blt',
                'Rooms': 'rooms',
                'Bed Rooms': 'bed_rooms',
                'Total Value': 'tot_val',
                'Land Value': 'lan_val',
                'Improvements Value': 'imp_val',
                'Structure Hazard Risk Level': 'risk_category'
              };

              _.each(_.pairs(items), function(pair){
                var key = pair[0];
                var value = evt.feature.properties[pair[1]];

                if (key.indexOf('Value') !== -1 && value != null) {
                  value = $filter('currency')(value, '$', 0);
                }

                if ((key === 'Building Sq Footage' || key === 'Units') && value != null) {
                  value = $filter('number')(value, 0);
                }

                value = value ? value : 'Unknown';
                message += '<b>' + key + ':</b> ' + value + '</br>';
              });

              L.popup()
                .setLatLng(evt.latlng)
                .setContent(message)
                .openOn(args.map);
            }
          }
        });

        args.layersControl.addOverlay(parcelsLayer, 'Parcels');

        args.map.on('overlayadd', function(layer) {
          if (layer.layer._leaflet_id !== parcelsLayer._leaflet_id) {
            return;
          }

          if (args.onShow) {
            args.onShow(true);
          }
        })

        args.map.on('overlayremove', function(layer) {
          if (layer.layer._leaflet_id !== parcelsLayer._leaflet_id) {
            return;
          }

          if (args.onShow) {
            args.onShow(false);
          }
        });

        if (args.onInit) {
          args.onInit(parcelsLayer);
        }
      },
    };
  }
})();
