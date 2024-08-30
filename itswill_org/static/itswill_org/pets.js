
function toggleDropRateInfo(event)
{
  var show = $(event.target).is(":checked");

  $(".pet-droprateinfo").css({
    "display": show ? "block" : "none",
  });

  if (show)
  {
    $(".absurdly-lucky").css({
      "background-color": "#26B661",
      "color": "var(--bg)"
    });
    $(".very-lucky").css({
      "background": "#63D49C",
      "color": "var(--bg)",
    });
    $(".lucky").css({
      "background": "#89DC4C",
      "color": "var(--bg)",
    });
    $(".on-rate").css({
      "background": "#EDCE35",
      "color": "var(--bg)",
    });
    $(".unlucky").css({
      "background": "#EF8924",
      "color": "var(--bg)",
    });
    $(".very-unlucky").css({
      "background": "#EF5E1B",
      "color": "var(--bg)",
    });
    $(".absurdly-unlucky").css({
      "background": "#EF3711",
      "color": "var(--bg)",
    });
  }
  else 
  {
    $(".absurdly-lucky, .very-lucky, .lucky, .on-rate, .unlucky, .very-unlucky, .absurdly-unlucky").css({
      "background": "",
      "color": "",
    })
  }
}

$(window).on('load', function() {

  toggleDropRateInfo({ "target": $("#enable-droprateinfo") })

  $("#enable-droprateinfo").change((e) => {
    toggleDropRateInfo(e);
  });

});