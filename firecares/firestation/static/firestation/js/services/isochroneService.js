'use strict';

(function () {
    angular.module('fireStation.isochroneService', [])
        .factory('isochroneService', IsochroneService);


    IsochroneService.$inject = ['$http', '$q', '$rootScope'];
    function IsochroneService($http, $q, $rootScope) {
        return {
            coorsArray: [],
            PROFILES: ['walking', 'cycling', 'driving'],
            profile: 'walking',
            minutes: 10,
            features: [],

            setProfile (profile) {
                this.profile = profile;
            },
            setMinutes (minutes) {
                this.minutes = minutes;
            },
            setCoorsArray(coorsArray) {
                this.coorsArray = coorsArray;
            },
            refreshIsochrones() {
                return new Promise((res,rej)=>{
                    this.features = [];
                    var promises = [];
                    for(var x in this.PROFILES)
                        promises = promises.concat(this.coorsArray.map((coors)=>{return this.getIsochrone(coors,this.PROFILES[x])}))
                    Promise.all(promises)
                    .then((data)=>{
                        
                        if(data && data.length > 0)
                            res(data.map(resp=>resp[0]));
                        else{
                            
                            res(data);
                        }     
                    })
                    .catch((ex)=>{
                        
                        res({'error':ex.toString()})
                    })
                })
            },

            getIsochrones(params={}){
                this.coorsArray = params.coorsArray ||this.coorsArray;
                this.profile = params.profile ||this.profile;
                this.minutes = params.minutes ||this.minutes;
                return this.refreshIsochrones();
            },


            /** fetch the census statistical data for the given state 
             * @param {String} stateAbbreviation
            */
            getIsochrone(coors,profile=this.profile,minutes=this.minutes) {
                return new Promise((res, rej) => {
                    // Create variables to use in getIso()
                    var urlBase = 'https://api.mapbox.com/isochrone/v1/mapbox/';

                    var lon = coors[0];
                    var lat = coors[1];
                    var query =
                        urlBase +
                        profile +
                        '/' +
                        lon +
                        ',' +
                        lat +
                        '?contours_minutes=' +
                        minutes +
                        '&polygons=true&access_token=' +
                        'pk.eyJ1IjoiZGF2aWRwbHVtbWVyLXBlIiwiYSI6ImNrY201aHhzYTAwdmozMG5uNnVhenJkemQifQ.qENAxqiz4fiHaRj9abujSw';

                    $.ajax({
                        method: 'GET',
                        url: query
                    }).done(function (data) {
                        // Set the 'iso' source's data to what's returned by the API query
                        // map.getSource('iso').setData(data);

                        res(data.features)
                    });
                })


            }
              
            


        }
    }

})()
