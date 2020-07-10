"use strict";

(function () {
  angular
    .module("fireStation.censusService", [])
    .factory("census", CensusService);

  CensusService.$inject = ["$http", "$q", "$rootScope"];
  function CensusService($http, $q, $rootScope) {
    return {
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
          try{
            for (var x in this.stateCodes) {
            if (x == abbreviation) return this.stateCodes[x].id;
            }
        }catch(ex){ 
            console.error(ex);
            return null; }
      },

      /** fetch the census statistical data for the given state
       * @param {String} stateAbbreviation
       */
      getTractData(stateAbbreviation) {
        return new Promise((res, rej) => {
            
          var stateId = this.stateAbbreviationToCode(stateAbbreviation);
          if(!stateId){
              return res({
                  'success':false,
                  'error':'The state ID is invalid.'
              })
          }
          $http({
            method: "GET",
            url:
              "https://api.census.gov/data/2017/acs/acs5?get=NAME,B01001_001E&in=state:" +
              stateId +
              "%20county:*&for=tract:*&key=655fd4220567937e8b2c8f1041dbe01696457797",
          }).then(
            async (resp) => {
              //convert the successful response from a string array into a json array
              if (resp.status == 200 && resp.data?.length > 1) {
                var data = [];
                var densityData = await this.getCountyDensityData(stateId);

                for (var x = 1; x < resp.data.length; x++) {
                  var e = {};
                  for (var i in resp.data[0]) {
                    e[resp.data[0][i]] = resp.data[x][i];
                  }
                  e.DENSITY = densityData[e.state + e.county];
                  data.push(e);
                }

                res((await this.generateLayerJSON(data)));
              } else {
                rej();
              }
            },
            (error) => {
              rej(error);
            }
          );
        });
      },

      /**
       * retrieve the population density data for all counties in the given state
       * @param {String} stateId
       */
      getCountyDensityData(stateId) {
        return new Promise((res, rej) => {
          $http({
            method: "GET",
            url:
              "https://api.census.gov/data/2019/pep/population" +
              "?get=COUNTY,STATE,DENSITY,POP,NAME&for=county:*" +
              "&in=state:" +
              stateId,
          }).then(
            (resp) => {
              //convert the successful response from a string array into a json array
              if (resp.status == 200 && resp.data?.length > 1) {
                var data = [];
                for (var x = 1; x < resp.data.length; x++) {
                  var e = {};
                  for (var i in resp.data[0]) {
                    e[resp.data[0][i]] = resp.data[x][i];
                  }
                  data.push(e);
                }
                var densityData = {};
                for (var x in data) {
                  densityData[data[x].state + data[x].county] = data[x].DENSITY;
                }

                res(densityData);
              } else rej();
            },
            (error) => {
              rej(error);
            }
          );
        });
      },

      /**
       * Take the given statistical data and build a layer with it
       * @param {Object} response
       */
      generateLayerJSON(response) {
        return new Promise((res, rej) => {
          //extract the density values

          var values = response
            .map(function (county) {
              //return Math.random() * 33;

              return parseFloat(county.DENSITY);
            })
            .sort((a, b) => a - b);

          //define the color scale for the features
          var colorScale = chroma.scale(["#cccccc", "#ff0000"]).domain(values);
          function getColor(val) {
            return colorScale(val).alpha(1).css();
          }

          //generate style expressions for each of the features
          var colorJSON = {};
          var colors = {};
          var GEOIDs = [];
          response.forEach((county) => {
            var GEOID = county.state + county.county + county.tract;
            GEOIDs.push(GEOID);
            var value = county.DENSITY;
            var color = getColor(value);
            if (!colors[color]) {
              colors[color] = [];
            }
            colors[color].push(GEOID);
          });
          var colorExpression = ["match", ["get", "GEOID"]];
          Object.entries(colors).forEach(function ([color, GEOIDs]) {
            colorExpression.push(GEOIDs, color);
            GEOIDs.forEach((item) => {
              colorJSON[item] = color;
            });
          });
          colorExpression.push("rgba(0,0,0,0)");

          // return the layer json
          res({
            url:
              "https://gis-server.data.census.gov/arcgis/rest/services/Hosted/VT_2018_140_00_PY_D1/VectorTileServer/tile/{z}/{y}/{x}.pbf",

            /** only keep the features with in the selected state */
            filter(feature) {
              if (GEOIDs.indexOf(feature.properties.GEOID) > -1) return true;
              else return false;
            },
            /** set the color for each feature in the layer */
            style(feature) {
              return {
                color: colorJSON[feature.properties.GEOID],
                outline: {
                  color: "#ffffff",
                  size: 1,
                },
              };
            },
          });
        });
      },
    };
  }
})();
