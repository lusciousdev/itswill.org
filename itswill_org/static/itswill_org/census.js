const data = document.currentScript.dataset;

const jsonPath = data.jsonpath;

Chart.defaults.color = "#efeff1";

slideshow_indexes = {}

function incrementSlide(slideshowId, n) {
  slideshow_indexes[slideshowId] += n;
  showSlide(slideshowId);
}

function goToSlide(slideshowId, n) {
  slideshow_indexes[slideshowId] = n
  showSlide(slideshowId);
}

function showSlide(slideshowId) {
  var sc = $("#{0}".format(slideshowId))
  
  var slides = sc.find(".slide");
  var dots = sc.find(".slideshow-dot");

  var idx = slideshow_indexes[slideshowId]

  if (idx >= slides.length) {
    slideshow_indexes[slideshowId] = 0;
  }

  if (idx < 0) {
    slideshow_indexes[slideshowId] = slides.length - 1;
  }
  
  idx = slideshow_indexes[slideshowId]

  slides.css({ "display": "none" });
  dots.removeClass("active");

  $(slides[idx]).css({ "display": "block" });
  $(dots[idx]).addClass("active");
} 

function addDots() {
  $(".slideshow-container").each((i, element) => {
    var slideshowID = $(element).attr('id');
    
    slideshow_indexes[slideshowID] = 0;

    var dotContainer = $($(element).find('.dot-container')[0]);

    $(element).find(".prev-slide").click(function () { incrementSlide(slideshowID, -1); });
    $(element).find(".next-slide").click(function () { incrementSlide(slideshowID, 1); });

    for (var i = 0; i < $(element).find(".slide").length; i++)
    {
      dotContainer.append("<span class='slideshow-dot' onclick='goToSlide(\"{0}\", {1})'></span>".format(slideshowID, i));
    }

    showSlide(slideshowID)
  });
}

$(window).on('load', function() {

  addDots();

  chart_data = {};

  fetch(jsonPath).then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }).then(data => {
    chart_data = data;

    for (var key in chart_data["charts"])
    {
      title = chart_data["charts"][key]["title"];
      subtitle = chart_data["charts"][key]["subtitle"];
      d = chart_data["charts"][key]["data"];
      d["options"]["plugins"]["tooltip"] = { 
        callbacks: {
          label: function(ctx) {
            var total = ctx.dataset.responses;
            var currentValue = ctx.dataset.data[ctx.dataIndex];
            var percentage = Math.floor(((currentValue/total) * 1000)+0.5)/10;
            return " " + percentage + "% (" + currentValue + ")";
          }
        }
      }
  
      const chart = new Chart("{0}".format(key), d);
      $("#{0}-title".format(key)).html(title)
      $("#{0}-subtitle".format(key)).html(subtitle)
    }
  });
});