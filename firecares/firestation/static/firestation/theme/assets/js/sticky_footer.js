$(function() {
  $(window).on('resize', function() {
    var height = $(window).height();
    if ( height > $('#ct-js-wrapper').height() + 80 && height > 980 && $(window).width() >= 1200) {
      $('footer').css({position: 'absolute', bottom: '80px', width: '100%'});
      $('.ct-postFooter').css({position: 'absolute', bottom: 0, width: '100%'});
    }
    else {
      $('footer').removeAttr('style');
      $('.ct-postFooter').removeAttr('style');
    }
  });

  $(window).trigger('resize');
});
