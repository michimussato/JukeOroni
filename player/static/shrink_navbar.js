$(window).on("scroll", function(e) {
 if(window.scrollY > 0){
   $('#navbar').addClass('tiny');
 }
 else{
   $('#navbar').removeClass('tiny');
 }
});
