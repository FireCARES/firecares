'use strict';

(function() {

    angular.module('fireStation.search', ['ui.select', 'ngSanitize'])

    .directive('search', function() {
            return {
                restrict: 'C',
                link: function (scope, element, attrs) {
                    scope.params = {};
                    scope.sortFields = [];
                    scope.limits = [15, 30, 60, 90];
                    
                    attrs.$observe('fdid', function() {
                      scope.params.fdid = attrs.fdid;
                    });

                    attrs.$observe('state', function() {
                      scope.params.state = attrs.state;
                    });

                    attrs.$observe('name', function() {
                      scope.params.name = attrs.name;
                    });

                    attrs.$observe('region', function() {
                      scope.params.region = attrs.region;
                    });


                    attrs.$observe('population', function() {
                      scope.params.population = attrs.population;
                    });

                    attrs.$observe('q', function() {
                      scope.params.q = attrs.q;
                    });


                   attrs.$observe('distModelScore', function() {
                      scope.params.dist_model_score = attrs['distModelScore']; 
                   });


                    attrs.$observe('sortBy', function() {
                      scope.params.sortBy = attrs['sortBy'];
                    });

                    attrs.$observe('limit', function() {
                      scope.params.limit = attrs['limit'];
                    });

                    attrs.$observe('sortFields', function() {
                      scope.sortFields =  scope.$eval(attrs['sortFields']);
                    });

                    scope.states = [{"abbr": "Any", "name": "Any"}, {"abbr": "WA", "name": "Washington"}, {"abbr": "DE", "name": "Delaware"}, {"abbr": "DC", "name": "District of Columbia"}, {"abbr": "WI", "name": "Wisconsin"}, {"abbr": "WV", "name": "West Virginia"}, {"abbr": "HI", "name": "Hawaii"}, {"abbr": "FL", "name": "Florida"}, {"abbr": "WY", "name": "Wyoming"}, {"abbr": "NH", "name": "New Hampshire"}, {"abbr": "NJ", "name": "New Jersey"}, {"abbr": "NM", "name": "New Mexico"}, {"abbr": "TX", "name": "Texas"}, {"abbr": "LA", "name": "Louisiana"}, {"abbr": "NC", "name": "North Carolina"}, {"abbr": "ND", "name": "North Dakota"}, {"abbr": "NE", "name": "Nebraska"}, {"abbr": "TN", "name": "Tennessee"}, {"abbr": "NY", "name": "New York"}, {"abbr": "PA", "name": "Pennsylvania"}, {"abbr": "CA", "name": "California"}, {"abbr": "NV", "name": "Nevada"}, {"abbr": "VA", "name": "Virginia"}, {"abbr": "CO", "name": "Colorado"}, {"abbr": "AK", "name": "Alaska"}, {"abbr": "AL", "name": "Alabama"}, {"abbr": "AR", "name": "Arkansas"}, {"abbr": "VT", "name": "Vermont"}, {"abbr": "IL", "name": "Illinois"}, {"abbr": "GA", "name": "Georgia"}, {"abbr": "IN", "name": "Indiana"}, {"abbr": "IA", "name": "Iowa"}, {"abbr": "OK", "name": "Oklahoma"}, {"abbr": "AZ", "name": "Arizona"}, {"abbr": "ID", "name": "Idaho"}, {"abbr": "CT", "name": "Connecticut"}, {"abbr": "ME", "name": "Maine"}, {"abbr": "MD", "name": "Maryland"}, {"abbr": "MA", "name": "Massachusetts"}, {"abbr": "OH", "name": "Ohio"}, {"abbr": "UT", "name": "Utah"}, {"abbr": "MO", "name": "Missouri"}, {"abbr": "MN", "name": "Minnesota"}, {"abbr": "MI", "name": "Michigan"}, {"abbr": "RI", "name": "Rhode Island"}, {"abbr": "KS", "name": "Kansas"}, {"abbr": "MT", "name": "Montana"}, {"abbr": "MS", "name": "Mississippi"}, {"abbr": "SC", "name": "South Carolina"}, {"abbr": "KY", "name": "Kentucky"}, {"abbr": "OR", "name": "Oregon"}, {"abbr": "SD", "name": "South Dakota"}];
                    scope.regions = ['Any', 'Midwest', 'South', 'West'];

                    scope.search = function() {
                        window.location = window.location.pathname + '?' + $.param( scope.params );
                      }
                    }

            };
        })

    .directive('ngEnter', function () {
        return function (scope, element, attrs) {
            element.bind("keydown keypress", function (event) {
                if(event.which === 13) {
                    scope.$apply(function (){
                        scope.$eval(attrs.ngEnter);
                    });

                    event.preventDefault();
                }
            });
        };
    });

})();

