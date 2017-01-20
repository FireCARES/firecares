'use strict';

(function() {
  angular.module('fireStation.departmentDetailController.whitelistAdmin', [])
    .controller('whitelistAdminController', WhitelistAdminController);

  WhitelistAdminController.$inject = ['$scope', 'limitToFilter', '$http', '$timeout'];

  function WhitelistAdminController($scope, limitToFilter, $http, $timeout) {
    $scope.departmentWhitelists = window.departmentWhitelists;
    $scope.toAdd = null;

    var oldEmail = null;

    $scope.addWhitelist = function() {
      $scope.toAdd = {
        email_or_domain: '',
        is_domain_whitelist: false
      };
      $timeout(function() {
        angular.element('input[name="email_or_domain"]').focus();
      });
    };

    $scope.$watch('toAdd.is_domain_whitelist', function(newValue, oldValue) {
      if (newValue) {
        oldEmail = $scope.toAdd.email_or_domain;
        $scope.toAdd.email_or_domain = toDomainWhitelist($scope.toAdd.email_or_domain);
      }
      else {
        if ($scope.toAdd && oldEmail) {
          $scope.toAdd.email_or_domain = oldEmail;
        }
      }
    });

    var toDomainWhitelist = function(email) {
      return email.replace(/[^@]+@/, '');
    };

    var reset = function() {
      $scope.toAdd = null;
      oldEmail = null;
    };

    $scope.deleteItem = function(item) {
      var i = _.findWhere($scope.departmentWhitelists, item);
      if (!_.isUndefined(i)) {
        $scope.departmentWhitelists.splice($scope.departmentWhitelists.indexOf(i), 1);
      }
    };

    $scope.addComplete = function() {
      if ($scope.toAdd.is_domain_whitelist) {
        $scope.toAdd.email_or_domain = toDomainWhitelist($scope.toAdd.email_or_domain);
      }
      $scope.departmentWhitelists.push($scope.toAdd);
      reset();
    };

    $scope.cancelAdd = function() {
      reset();
    };

    $scope.alreadyExists = function(item) {
      return !_.isEmpty(_.findWhere($scope.departmentWhitelists, item));
    };
  }
})();
