'use strict';

(function() {
    angular.module('fireStation.feedback', [])
      .config(['$uibTooltipProvider', function ($uibTooltipProvider) {
        // Set custom options on popover
        $uibTooltipProvider.options({
            placement: 'bottom',
            appendToBody: true,
            class: 'form-popover'
        })
      }])
      .directive('feedback', function($http, $compile) {
        return {
          restrict: 'E',
          transclude: true,
          scope: {
            url: '@',
            csrftoken: '@',
            user: '@',
            firedepartment: '@',
            firestation: '@'
          },
          templateUrl: '/static/firestation/js/directives/partial/feedback/feedback.tpl.html',
          link: function(scope, element, attrs) {
            // Initialize form data with current values
            scope.formData = {
              'csrfmiddlewaretoken': scope.csrftoken,
              'user': scope.user,
              'department': scope.firedepartment,
              'firestation': scope.firestation,
              'message': ''
            };

            // Set form statuses
            scope.sendingForm = false
            scope.formSent = false;
            scope.successForm = false;
            scope.popOverIsOpen = false;

            scope.togglePopOver = function() {
              scope.popOverIsOpen = !scope.popOverIsOpen;
              scope.formSent = false;
              scope.successForm = false;
            }

            // Process form
            scope.processForm = function(isValid) {
              scope.sendingForm = true;
              $http.post(scope.url, $.param(scope.formData), {
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
              }).then(function(data) {
                scope.formSent = true;
                scope.sendingForm = false;
                scope.successForm = true;
                scope.formData.message = ''
              }, function(data) {
                scope.sendingForm = false;
                scope.formSent = true;
                scope.successForm = false;
              });
            }
          }
        }
      })
    ;
})();
