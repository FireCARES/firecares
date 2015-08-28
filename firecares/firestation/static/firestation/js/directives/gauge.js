'use strict';

(function() {
  var module = angular.module('fireStation.gauge', []);

  module.filter('ordinal', function() {
      return function(i) {
            var j = i % 10,
                k = i % 100;
            if (j == 1 && k != 11) {
                return i + "st";
            }
            if (j == 2 && k != 12) {
                return i + "nd";
            }
            if (j == 3 && k != 13) {
                return i + "rd";
            }
            return i + "th";
        }
  });

  module.directive('gauge',
      function() {
        return {
          restrict: 'E',
          replace: true,
          templateUrl: '/static/firestation/js/directives/partial/gauge.tpl.html',
          scope: {
             metricTitle: '@?',
             description: '@?',
             value: '@?',
             min: '@?',
             max: '@?',
             learnMore: '@?'
          },
          // The linking function will add behavior to the template
          link: function(scope, element, attrs) {
            var element = element;
            var needle = $(element[0].querySelector('.needle'));
            scope.inverse = attrs.hasOwnProperty('inverse');

            // the pickHex function (from less.js) takes rgb values
            var green = [116, 172, 73];
            var yellow = [254, 190, 0];
            var red = [246, 84, 47];

           function pickHex(color1, color2, weight) {
                var p = weight;
                var w = p * 2 - 1;
                var w1 = (w/1+1) / 2;
                var w2 = 1 - w1;
                var rgb = [Math.round(color1[0] * w1 + color2[0] * w2),
                    Math.round(color1[1] * w1 + color2[1] * w2),
                    Math.round(color1[2] * w1 + color2[2] * w2)];
                return rgb;
            }

            scope.$watch('value', function() {
               var color;
               var location = scope.value / (scope.max - scope.min);
               var needleRotation = (180 * location) - 90;

               // the setTimeout helps with the transition effect.
               setTimeout(function() {
                   needle.css({transform: 'rotate(' + needleRotation + 'deg)'});
               }, 1);

               if (location < .5) {
                color = pickHex(yellow, green, location / .5);
               } else {
                color = pickHex(red, yellow, (location - .5) /.5);
               }

               var colorString = 'rgb('+color[0] + ',' + color[1] + ',' + color[2] +')';
               $('.gauge-result-color').css({'background': colorString});
               needle.css({'border-bottom': '60px solid ' + colorString});
            });

          }
        };
      });

  module.directive('barGauge',
      function() {
        return {
          restrict: 'E',
          replace: true,
          templateUrl: '/static/firestation/js/directives/partial/bar-gauge.tpl.html',
          scope: {
             value: '@?',
             min: '@?',
             max: '@?'
          },
          // The linking function will add behavior to the template
          link: function(scope, element, attrs) {
            var element = element;
            var gauge = $(element[0].querySelector('.bar-gauge'));
            var needle = $(element[0].querySelector('.bar-gauge-needle'));
            scope.inverse = attrs.hasOwnProperty('inverse');

            scope.$watch('value', function() {
               if (scope.min == null || scope.min === '' || scope.max == null || scope.max === ''
                   || scope.value == null || scope.value === '') {
                 needle.css({display: 'none'});
                 return
               } else {
                 var location = scope.value / scope.max;
                 needle.css({left: location * (gauge.width() - 5) + 'px'});
               }
            });

          }
        };
      });

    module.directive('numberGauge',
      function() {
        return {
          restrict: 'E',
          replace: true,
          templateUrl: '/static/firestation/js/directives/partial/number-gauge.tpl.html',
          scope: {
             value: '@',
             metricTitle: '@?',
             description: '@?'
          },
          // The linking function will add behavior to the template
          link: function(scope, element, attrs) {
            scope.inverse = attrs.hasOwnProperty('inverse');
            scope.color = '#f6542f';

            if (scope.value === '1') {
                scope.color = "#74AC49";
            } else if (scope.value === '2') {
                scope.color = "#CBB71B";
            } else if (scope.value === '3') {
                scope.color = "#FA9014";
            }

          }
        };
      });

    module.filter('numberGaugePosition', function() {
      return function(i) {
            if (i === 1) {
                return 'lowest';
            } else if (i === 2) {
                return 'second lowest';
            } else if (i === 3) {
                return 'second highest';
            } else if (i === 4) {
                return 'highest';
            }
        }
  });
}());


