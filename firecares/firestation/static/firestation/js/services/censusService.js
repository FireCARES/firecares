"use strict";

(function () {
    angular
        .module("fireStation.censusService", [])
        .factory("census", CensusService);

    CensusService.$inject = ["$http", "$q", "$rootScope"];
    function CensusService($http, $q, $rootScope) {
        return {
            COLORS: {
                U: "rgba(100,172,255,1)",//urban area
                R: "rgba(164,255,164,1)",//rural area
                default: "rgba(164,255,164,1)",//unknown area (sometimes the api returns a null value for UR)
            },
            stateCodes: {
                AL: { id: "01", name: "Alabama" },
                AK: { id: "02", name: "Alaska" },
                AZ: { id: "04", name: "Arizona" },
                AR: { id: "05", name: "Arkansas" },
                CA: { id: "06", name: "California" },
                CO: { id: "08", name: "Colorado" },
                CT: { id: "09", name: "Connecticut" },
                DE: { id: "10", name: "Delaware" },
                FL: { id: "12", name: "Florida" },
                GA: { id: "13", name: "Georgia" },
                HI: { id: "15", name: "Hawaii" },
                ID: { id: "16", name: "Idaho" },
                IL: { id: "17", name: "Illinois" },
                IN: { id: "18", name: "Indiana" },
                IA: { id: "19", name: "Iowa" },
                KS: { id: "20", name: "Kansas" },
                KY: { id: "21", name: "Kentucky" },
                LA: { id: "22", name: "Louisiana" },
                ME: { id: "23", name: "Maine" },
                MD: { id: "24", name: "Maryland" },
                MA: { id: "25", name: "Massachusetts" },
                MI: { id: "26", name: "Michigan" },
                MN: { id: "27", name: "Minnesota" },
                MS: { id: "28", name: "Mississippi" },
                MO: { id: "29", name: "Missouri" },
                MT: { id: "30", name: "Montana" },
                NE: { id: "31", name: "Nebraska" },
                NV: { id: "32", name: "Nevada" },
                NH: { id: "33", name: "New Hampshire" },
                NJ: { id: "34", name: "New Jersey" },
                NM: { id: "35", name: "New Mexico" },
                NY: { id: "36", name: "New York" },
                NC: { id: "37", name: "North Carolina" },
                ND: { id: "38", name: "North Dakota" },
                OH: { id: "39", name: "Ohio" },
                OK: { id: "40", name: "Oklahoma" },
                OR: { id: "41", name: "Oregon" },
                PA: { id: "42", name: "Pennsylvania" },
                RI: { id: "44", name: "Rhode Island" },
                SC: { id: "45", name: "South Carolina" },
                SD: { id: "46", name: "South Dakota" },
                TN: { id: "47", name: "Tennessee" },
                TX: { id: "48", name: "Texas" },
                UT: { id: "49", name: "Utah" },
                VT: { id: "50", name: "Vermont" },
                VA: { id: "51", name: "Virginia" },
                WA: { id: "53", name: "Washington" },
                WV: { id: "54", name: "West Virginia" },
                WI: { id: "55", name: "Wisconsin" },
                WY: { id: "56", name: "Wyoming" },
                PR: { id: "72", name: "Puerto Rico" },
            },
            /**
             * Fetch the state code for the given abbreviation
             * @param {String} abbreviation
             */
            stateAbbreviationToCode(abbreviation) {
                try {
                    for (var x in this.stateCodes) {
                        if (x == abbreviation) return this.stateCodes[x].id;
                    }
                } catch (ex) {
                    console.error(ex);
                    return null;
                }
            },

            /** fetch the census statistical data for the given state
             * and return a vector tile layer in JSON format
             * @param {String} stateAbbreviation
             */
            getTractData(stateAbbreviation) {
                return new Promise((res, rej) => {

                    var stateId = this.stateAbbreviationToCode(stateAbbreviation);
                    if (!stateId) {
                        return res({
                            'success': false,
                            'error': 'The state ID is invalid.'
                        })
                    }
                    //get the list of tracts for the selected state
                    $http({
                        method: "GET",
                        url:
                            "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/10/query?" +
                            "where=STATE=" + stateId + "&f=pjson&outFields=STATE,COUNTY,TRACT,UR&returnGeometry=false"
                    }).then(
                        (resp) => {

                            //return an error if no features could be found
                            if (resp.status != 200 || resp.data?.features?.length <= 0) {
                                res({
                                    success: false,
                                    error: "No map data could be found for the selected state."
                                })
                            } else {
                                var features = {};
                                //assign colors to each of the features based on its rural/urban classification
                                for (var x in resp.data.features) {
                                    let data = resp.data.features[x].attributes;
                                    features[(data.STATE + data.COUNTY + data.TRACT)] = this.COLORS[data.UR] || this.COLORS.default
                                }

                                // return the layer json
                                res({
                                    url:
                                        "https://gis-server.data.census.gov/arcgis/rest/services/Hosted/VT_2018_140_00_PY_D1/VectorTileServer/tile/{z}/{y}/{x}.pbf",

                                    /** only keep the features within the selected state */
                                    filter(feature) {
                                        return !!features[feature.properties.GEOID];
                                    },
                                    /** set the color for each feature in the layer */
                                    style(feature) {
                                        return {
                                            color: features[feature.properties.GEOID]
                                        };
                                    },

                                });
                            }
                        },
                        (error) => {
                            rej(error)
                        }
                    )
                })
            },

        };
    }
})();
