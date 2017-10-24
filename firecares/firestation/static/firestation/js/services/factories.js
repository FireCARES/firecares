'use strict';

(function() {
    angular.module('fireStation.factories', ['ngResource'])

    .factory('FireStation', function ($resource) {
        return $resource('/api/v1/firestations/:id/', {},
            {
                'query': {'method': 'GET', isArray: false},
                'update': { method: 'PUT' }

        });
    })

    .factory('FireStationandStaffing', function ($resource) {
        return $resource('/api/v1/staffingstations/:id/', {id: '@id'},
            {
                'query': {'method': 'GET', isArray: false}

        });
    })

    .factory('FireDepartment', function ($resource) {
        return $resource('/api/v1/fire-departments/:id/', {id: '@id'},
          {
            'query': {
              'method': 'GET',
              isArray: false
            },
            'update': {
              'method': 'PUT'
            }
          });
    })

    .factory('WeatherWarning', function ($resource) {
        return $resource('/api/v1/weather-warning/:id/', {id: '@id'},
          {
            'query': {
              'method': 'GET',
              isArray: false
            }
          });
    })

    .factory('USGSUnit', function ($resource) {
        return $resource('/api/v1/usgs/:id/', {}, {'query': {'method': 'GET', isArray: false}});
    })

    .factory('ServiceAreaRollup', function ($resource) {
        return $resource('/api/v1/getserviceareainfo/:id/', {}, {'query': {'method': 'GET', isArray: false}});
    })

    .factory('Staffing', function ($resource) {
        return $resource('/api/v1/staffing/:id/', {},
            {query: { method: 'GET', isArray: true,
                transformResponse: function (jsondata) {
                    return JSON.parse(jsondata).objects;
                }
            },
                update: {method: 'PUT'}
            });
    })
})();
