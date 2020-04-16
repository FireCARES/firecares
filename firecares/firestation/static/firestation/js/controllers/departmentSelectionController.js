'use strict';

(function() {
  angular.module('fireStation.departmentSelection', [])
    .controller('departmentSelectionController', DepartmentSelectionController);

  DepartmentSelectionController.$inject = ['$scope', '$http'];

  function DepartmentSelectionController($scope, $http) {
    $scope.department_states = window.states;
    $scope.input = {
      department: null,
      state: null
    };
    $scope.departments = [];
    $scope.loading = false;
    $scope.$watch('input.state', function(val) {
      if (val) {
        $scope.loading = true;
        $scope.departments = null;
        $http({
          method: 'GET',
          url: '/api/v1/fire-departments/?limit=2000&fields=id,name&state=' + val
        }).then(function successCallback(response) {
          $scope.departments = response.data.objects;
          $scope.loading = false;
        }, function errorCallback(response) {
        });
      }
    });
  }
})();
