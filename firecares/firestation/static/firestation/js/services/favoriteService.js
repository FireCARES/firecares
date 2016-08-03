'use strict';

// AngularJS button click handler service
// to add a favorite button use the template tag:
//     {% favorite_button object %}
// load the tag with:
//     {% load favit_tags %}
// the tag is using an HTML fragment at:
//     firecares/template/favit/button.html (uses favoriteController and calls onFavorite on click)
(function () {
    angular.module('fireStation.favoriteService', [])
        .service('favorite', FavoriteService)
        .controller('favoriteController', FavoriteController)
    ;

    // The controller is used in the HTML fragment
    FavoriteController.$inject = ['$scope', 'favorite'];
    function FavoriteController($scope, favorite) {
        $scope.onFavorite = favorite.onFavorite;
        $scope.initFavoriteButtonColor = favorite.initFavoriteButtonColor;
    }

    // The service sends a POST request to favit and manages the button HTML elements
    FavoriteService.$inject = ['$http'];
    function FavoriteService($http) {

        var selected_color = '#FEBE00'
        var unselected_color = 'silver' // TEST this should be empty string
        var icon_id = 'favorite-star-' // + id (id prevents multiple favorite buttons on the same page from colliding)

        var disabled = []; // object ids that are currently being processed (TODO maybe its better to store this flag on the button element somehow?)

        this.initFavoriteButtonColor = function (id, selected) {
            var star = angular.element(document.getElementById(icon_id+id));
            star.css('color', selected == 'True' ? selected_color : unselected_color);
        };

        this.onFavorite = function (model, id) {
            if (disabled.indexOf(id) != -1) // if this object is currently being processed disable additional requests
                return;
            //console.log("Favorite an object for the current user, object id:" + id + " object model: " + model);
            disabled.push(id); // disable further requests for this object
            var star = angular.element(document.getElementById(icon_id+id));
            // flip the visual selection indication of the button immediately so the input feels responsive
            star.css('color', star.css('color') == selected_color ? unselected_color : selected_color);
            $http({
                method: 'POST',
                url: '/favit/add-or-remove',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // this is required to pass the request.is_ajax() test in favit
                },
                data: {
                    target_model: model,
                    target_object_id: id
                },
            }).then(function success(resp) {
                //console.log(resp); // resp.data.fav_count
                if (resp.data.status == 'added') {
                    console.log('favorite added');
                    star.css('color', selected_color);
                } else {
                    console.log('favorite removed');
                    star.css('color', unselected_color);
                }
                disabled.splice(disabled.indexOf(id), 1); // enable requests for this object
            }, function error(err) {
                console.error(err);
                disabled.splice(disabled.indexOf(id), 1); // enable requests for this object
            });
        };
    }
})();
