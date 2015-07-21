(function ($) {
    "use strict";

    /* ==== GOOGLE MAP ==== */

    var mapStyles = [{"featureType":"administrative","elementType":"labels.text.fill","stylers":[{"color":"#444444"}]},{"featureType":"landscape","elementType":"all","stylers":[{"color":"#f2f2f2"}]},{"featureType":"poi","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"road","elementType":"all","stylers":[{"saturation":-100},{"lightness":45}]},{"featureType":"road.highway","elementType":"all","stylers":[{"visibility":"simplified"}]},{"featureType":"road.arterial","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"transit","elementType":"all","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"all","stylers":[{"color":"#425a68"},{"visibility":"on"}]}];

    function initmap() {

        if (($(".ct-js-googleMap").length > 0) && (typeof google === 'object' && typeof google.maps === 'object')) {

            var draggable = true;

            if (device.mobile() || device.tablet()) {
                draggable = false;
            }

            $('.ct-js-googleMap--single').each(function () {
                var atcenter = "";
                var $this = $(this);
                var location = $this.data("location");
                var zoom = $this.data("zoom");
                var icongmap = $this.attr('data-icon');
                var markerDraggable = parseBoolean($this.attr('data-markerDraggable'), false);
                var offset = -30;
                var offsety = -20;
                var autoGPSselector = $('.ct-latlngAuto');
                var autoGPSlat = autoGPSselector.find('.latidude');
                var autoGPSlng = autoGPSselector.find('.longitude');

                if(markerDraggable!=true){
                    markerDraggable = false
                }

                if (validatedata($this.data("offset"))) {
                    offset = $this.data("offset");
                }

                if (validatedata($this.data("offsety"))) {
                    offsety = $this.data("offsety");
                }

                if (validatedata(location)) {
                    $this.gmap3({
                        marker: {
                            //latLng: [40.616439, -74.035540],
                            address: location, options: {
                                //visible: false
                                icon: new google.maps.MarkerImage(icongmap)
                            }, callback: function (marker) {
                                atcenter = marker.getPosition();
                                autoGPSlat.val(marker.getPosition().lat());
                                autoGPSlng.val(marker.getPosition().lng());
                                google.maps.event.addListener(marker, 'drag', function() {
                                    autoGPSlat.val(marker.getPosition().lat());
                                    autoGPSlng.val(marker.getPosition().lng())
                                });
                            }
                        }, map: {
                            options: {
                                //maxZoom:11,
                                zoom: zoom,
                                styles:mapStyles,
                                mapTypeId: google.maps.MapTypeId.ROADMAP, // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                scrollwheel: false,
                                disableDoubleClickZoom: false,
                                draggable: draggable, //disableDefaultUI: true,
                                disableDefaultUI: true,
                                mapTypeControlOptions: {
                                    //mapTypeIds: [google.maps.MapTypeId.ROADMAP, google.maps.MapTypeId.HYBRID],
                                    //style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                                    //position: google.maps.ControlPosition.RIGHT_CENTER
                                    mapTypeIds: []
                                }
                            }, events: {
                                idle: function () {
                                    if (!$this.data('idle')) {
                                        $this.gmap3('get').panBy(offset, offsety);
                                        $this.data('idle', true);
                                    }
                                }
                            }
                        }, overlay: {
                            address: location, options: {
                                offset: {
                                    y: -100, x: -25
                                }
                            }
                        }
                        //},"autofit"
                    });

                    // center on resize
                    google.maps.event.addDomListener(window, "resize", function () {
                        //var userLocation = new google.maps.LatLng(53.8018,-1.553);
                        setTimeout(function () {
                            $this.gmap3('get').setCenter(atcenter);
                            $this.gmap3('get').panBy(0, offset);
                        }, 400);

                    });

                    // set height
                    if($this.hasClass(".ct-googleMap-2col" && (device.mobile() || device.tablet()))){
                        $this.css("min-height", "600px");
                    }else{
                        $this.css("min-height", $this.data("height") + "px");
                    }
                }

                if ($this.parent().parent().hasClass('hidemap')) {
                    $this.parent().animate({height: '0px'}, 500);
                }

            }),
                jQuery('.ct-js-googleMap--group').each(function () {
                    var $this = jQuery(this);
                    var $display_desc = validatedata(parseBoolean($this.attr("data-display-desc")), false);
                    var dataMarkers= [];

                    if($display_desc == false){
                        $this.gmap3({
                            map:{
                                options:{
                                    center:[40.742803, -74.002424],
                                    zoom: 14,
                                    scrollwheel: false,
                                    disableDoubleClickZoom: false,
                                    draggable: draggable, //disableDefaultUI: true,
                                    disableDefaultUI: true,
                                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                                    // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                    styles:mapStyles
                                }
                            },
                            marker:{
                                values: [
                                    {
                                        address:"301 w 4th Street, New York",
                                        options:{
                                            icon: "assets/images/marker-villa.png"
                                        }
                                    },
                                    {
                                        address:"128 7th Ave S, New York",
                                        options:{
                                            icon: "assets/images/marker-apartment.png"
                                        }
                                    },
                                    {
                                        address:"Eve 55 W 8th St, New York",
                                        options:{
                                            icon: "assets/images/marker-commercial.png"
                                        }
                                    },
                                    {
                                        address:"21 W 16th St New York",
                                        options:{
                                            icon: "assets/images/marker-flat.png"
                                        }
                                    },
                                    {
                                        address:"Washington Square Fountain, New York",
                                        options:{
                                            icon: "assets/images/marker-house.png"
                                        }
                                    },
                                    {
                                        address:"Pinkberry - Chelsea 170 8th Ave, New York",
                                        options:{
                                            icon: "assets/images/marker-land.png"
                                        }
                                    },
                                    {
                                        address:"8 Charles Ln New York",
                                        options:{
                                            icon: "assets/images/marker-apartment.png"
                                        }
                                    },
                                    {
                                        address:"74 Green St Brooklyn",
                                        options:{
                                            icon: "assets/images/marker-commercial.png"
                                        }
                                    },

                                    {
                                        address:"321 w 4th Street, New York",
                                        options:{
                                            icon: "assets/images/marker-house.png"
                                        }
                                    }
                                ],
                                cluster:{
                                    radius: 50,
                                    0: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 53,
                                        height: 52
                                    },
                                    2: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 56,
                                        height: 55
                                    },
                                    50: {
                                        content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                        width: 66,
                                        height: 65
                                    }
                                }
                            }
                        })
                    } else{
                        $this.gmap3({
                            map:{
                                options:{
                                    center:[40.742803, -74.002424],
                                    zoom: 14,
                                    scrollwheel: false,
                                    disableDoubleClickZoom: false,
                                    draggable: draggable, //disableDefaultUI: true,
                                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                                    disableDefaultUI: true,
                                    styles:mapStyles
                                    // ('ROADMAP', 'SATELLITE', 'HYBRID','TERRAIN');
                                },
                                events:{
                                    click: function(map, event, context){
                                        gmap_clear_markers();
                                    }
                                }
                            }
                        })

                        //Ajax for JSon file
                        $.ajax({
                            url: "assets/js/gmaps/json/markers.json",
                            dataType: 'json',
                            type: 'POST',
                            success: function(data) {
                                dataMarkers = data.markers;
                                $.each(dataMarkers, function(key, val) {
                                    $this.gmap3({
                                        marker:{
                                            values:[{
                                                address:val.address,
                                                options:{
                                                    icon: val.icon
                                                },
                                                events: {
                                                    click: function() {
                                                        gmap_clear_markers();
                                                        $this.gmap3({
                                                            overlay:{
                                                                address:val.address,
                                                                options:{
                                                                    content: "<div class='ct-itemProducts ct-hover ct-itemProducts--boxed ct-gmapProduct animated activate fadeInDownSmall'>"+
                                                                    "<a href='product-single.html'>"+
                                                                    "<div class='ct-main-content'>" +
                                                                    "<div class='ct-imageBox'>"+
                                                                    "<img src='"+val.image+"' alt=''>"+
                                                                    "<i class='fa fa-eye'></i>"+
                                                                    "</div>"+
                                                                    "<div class='ct-main-text'>"+
                                                                    "<div class='ct-product--tilte'>"+
                                                                    val.address+
                                                                    "</div>"+
                                                                    "<div class='ct-product--price'>"+
                                                                    "<span>$ "+val.price+"</span>"+
                                                                        //"<span class='ct-price--Old'>$ 450,000</span>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "<div class='ct-product--meta'>"+
                                                                    "<div class='ct-status'><span class='ct-fw-600'>Status</span> "+val.status+"</div>"+
                                                                    "<div class='ct-icons'>"+
                                                                    "<span>"+
                                                                    "<i class='fa fa-bed'></i> "+
                                                                    val.bedrooms+
                                                                    "</span>"+
                                                                    "<span>"+
                                                                    "<i class='fa fa-cutlery'></i> "+
                                                                    val.bathrooms+
                                                                    "</span>"+
                                                                    "</div>"+
                                                                    "<div class='ct-text'>"+
                                                                    "<span> Area: <span>"+val.area+" m2</span></span>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "</div>"+
                                                                    "<div class='ct-bottomArrow'></div>"+
                                                                    "</a>"+
                                                                    "</div>",
                                                                    offset:{
                                                                        y:-340,
                                                                        x:-140
                                                                    }
                                                                }
                                                            }

                                                        });
                                                    }
                                                }
                                            }],
                                            cluster:{
                                                radius: 20,
                                                0: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 53,
                                                    height: 52
                                                },
                                                2: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 56,
                                                    height: 55
                                                },
                                                50: {
                                                    content: "<div class='ct-markerCluster'>CLUSTER_COUNT</div>",
                                                    width: 66,
                                                    height: 65
                                                }
                                            }
                                        }
                                    });
                                });

                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                console.log('ERROR', textStatus, errorThrown);
                            }
                        });

                    };
                    // Function Clear Markers
                    function gmap_clear_markers() {
                        $('.ct-gmapProduct').each(function() {
                            $(this).remove();
                        });
                    }


                    var map = $(".ct-js-googleMap").gmap3({
                        get: {
                            name:"map"
                        }
                    });

                    //Navigation

                    $('#zoomin').on("click", function(){
                        var newCenter = map.getZoom();
                        map.setZoom(newCenter+1);
                    })

                    $('#zoomout').on("click", function(){
                        var newCenter = map.getZoom();
                        map.setZoom(newCenter-1);
                    })

                    $('#geolocation').on("click", function(){
                        // Try HTML5 geolocation
                        if(navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(function(position) {
                                var pos = new google.maps.LatLng(position.coords.latitude,
                                    position.coords.longitude);

                                $(".ct-js-googleMap").gmap3({
                                    circle:{
                                        options:{
                                            center: pos,
                                            radius : 800,
                                            fillColor : "#60a7d4",
                                            strokeColor : "#333333"
                                        },
                                        callback: function(){
                                            $(this).gmap3('get').setZoom(15);
                                        }
                                    }
                                });

                                map.setCenter(pos);
                            }, function() {
                                handleNoGeolocation(true);
                            });
                        } else {
                            // Browser doesn't support Geolocation
                            handleNoGeolocation(false);
                        }
                    })

                    function handleNoGeolocation(errorFlag) {
                        if (errorFlag) {
                            var content = 'Error: The Geolocation service failed.';
                        } else {
                            var content = 'Error: Your browser doesn\'t support geolocation.';
                        }
                    }

                    function searchauto() {

                        var locations = [];

                        // Create the search box and link it to the UI element.
                        var input = (document.getElementById('searchGmaps'));

                        var searchBox = new google.maps.places.SearchBox(
                            /** @type {HTMLInputElement} */(input));

                        // Listen for the event fired when the user selects an item from the
                        // pick list. Retrieve the matching places for that item.

                        google.maps.event.addListener(searchBox, 'places_changed', function() {
                            var places = searchBox.getPlaces();


                            if (places.length == 0) {
                                return;
                            }
                            for (var i = 0, location; location = locations[i]; i++) {
                                location.setMap(null);
                            }

                            // For each place, get the icon, place name, and location.

                            locations = [];
                            var bounds = new google.maps.LatLngBounds();
                            for (var i = 0, place; place = places[i]; i++) {
                                var image = {
                                    url: "assets/images/marker-land.png",
                                    //size: new google.maps.Size(71, 71),
                                    origin: new google.maps.Point(0, 0),
                                    anchor: new google.maps.Point(17, 34)
                                    //scaledSize: new google.maps.Size(25, 25)
                                };

                                bounds.extend(place.geometry.location);
                            }

                            map.fitBounds(bounds);
                        });

                        google.maps.event.addListener(map, 'bounds_changed', function() {
                            var bounds = map.getBounds();
                            searchBox.setBounds(bounds);
                        });
                    }
                    searchauto();

                    if($this.hasClass(".ct-googleMap-2col" && (device.mobile() || device.tablet()))){
                        $this.css("min-height", "600px");
                    }else{
                        $this.css("min-height", $this.data("height") + "px");
                    }
                })
        }

    }

    initmap();

})(jQuery);



