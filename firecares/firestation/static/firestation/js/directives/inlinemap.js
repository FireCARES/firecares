'use strict';

(function() {
  var module = angular.module('fireStation.map', ['fireStation.factories', 'fireStation.mapService'])

  .directive('inlineMap', ['FireDepartment', 'USGSUnit', 'map', function(FireDepartment, USGSUnit, map) {
    return {
      restrict: 'E',
      scope: {
        overlayGeom: '@overlayGeom',
        overlayType: '@type'
      },
      template: '',
      link: function($scope, $element, attrs) {
        var overlay = JSON.parse($scope.overlayGeom);
        var curMap = map.initMap($element.get(0), {scrollWheelZoom: false});
        var layersControl = L.control.layers().addTo(curMap);

        var l = L.geoJson(config.geom, {
          style: function (feature) {
            return {color: '#6c6c6c', fillOpacity: .05, opacity: .8, weight: 2};
          }
        }).addTo(curMap);
        layersControl.addOverlay(l, 'Department Boundary');

        var headquartersGeom = config.headquarters ? L.latLng(config.headquarters.coordinates[1], config.headquarters.coordinates[0]) : null;
        var headquartersIcon = L.FireCARESMarkers.headquartersmarker();

        if ( headquartersGeom) {
          var headquarters = L.marker(headquartersGeom, {icon: headquartersIcon, zIndexOffset: 1000});
          headquarters.bindPopup('<b>' + config.headquartersName + '</b>').addTo(curMap);
          layersControl.addOverlay(headquarters, 'Headquarters Location');
        }

        var overlay = L.geoJson(overlay, {
          style: function (feature) {
            return {color: '#007f00', fillOpacity: .1, opacity:.8, weight:4};
          }
        }).addTo(curMap);
        layersControl.addOverlay(overlay, ($scope.overlayType || '') + ' Boundary');

        curMap.fitBounds(overlay.getBounds().extend(l.getBounds()), {});
      }
    };
  }]);
})();
