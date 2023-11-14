const { choices } = data;

var apiUrl = "https://leagues.itswill.org"

// First, checks if it isn't implemented yet.
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function xmlHttpRequestAsync(method, theUrl, callback, errorcb)
{
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.onreadystatechange = function() {
    if (xmlHttp.readyState == 4 && (xmlHttp.status >= 200 && xmlHttp.status < 300))
    {
      callback(xmlHttp.responseText);
    }
    else if(xmlHttp.readyState == 4)
    {
      errorcb(xmlHttp.responseText);
    }
  }
  xmlHttp.open(method, theUrl, true);
  xmlHttp.send(null);
}

function populateValueList()
{
  for (const key in choices)
  {
    var listId = "{0}-list".format(key);
    $("#value-list").append("<li>{0}</li>".format(key));
    $("#value-list").append("<ul class='tutorial-sublist' id='{0}'></ul>".format(listId));

    choices[key].choices.forEach(function(obj, index) {
      $("#{0}".format(listId)).append("<li><b>{0}</b> - <img class='value-img' src='{1}'> {2}</li>".format(index, obj.image, obj.name));
    });
  }
}

function setChoice(choiceid, choiceobj)
{
  $("#{0}-img".format(choiceid)).attr("src", choiceobj["image"])
  $("#{0}-name".format(choiceid)).html(choiceobj["name"])
}

function nextSection(sectionList, sectionIndex, speed = 1000)
{
  sectionList.each(function(index, obj) {
    if (index == sectionIndex)
    {
      $(obj).css('visibility', 'visible');
    }
    else
    {
      $(obj).css('visibility', 'hidden');
    }
  });
}

function handleGetUserResponse(text)
{
  var respJson = JSON.parse(text);

  setChoice("region1", choices.regions.choices[respJson["region1"]])
  setChoice("region2", choices.regions.choices[respJson["region2"]])
  setChoice("region3", choices.regions.choices[respJson["region3"]])

  setChoice("tier1", choices.tier1.choices[respJson["tier1"]])
  setChoice("tier2", choices.tier2.choices[respJson["tier2"]])
  setChoice("tier3", choices.tier3.choices[respJson["tier3"]])
  setChoice("tier4", choices.tier4.choices[respJson["tier4"]])
  setChoice("tier5", choices.tier5.choices[respJson["tier5"]])
  setChoice("tier6", choices.tier6.choices[respJson["tier6"]])
  setChoice("tier7", choices.tier7.choices[respJson["tier7"]])
}

function handleGetUserError(text)
{
  console.log("API Error: " + text);
}

function getUser(username)
{
  var reqUrl = apiUrl + "/api/v1/get?username=" + username
  xmlHttpRequestAsync("GET", reqUrl, handleGetUserResponse, handleGetUserError);
}

$(window).on('load', function () {
  var queryString = window.location.search;
  var urlParams = new URLSearchParams(queryString);
  var sectionList = $('.section');

  if (urlParams.has("carousel"))
  {
    $(".section-wrap").css({
      'display': 'grid',
      'grid-template': '1fr / 1fr',
      'place-items': 'center left'
    });
    $(".section-wrap > *").css({
      "grid-column": "1 / 1",
      "grid-row": "1 / 1"
    });

    nextSection(sectionList, 0, 0);
    var sectionIndex = 1;
    var sectionInterval = setInterval(function() 
    { 
      nextSection(sectionList, sectionIndex); 
      sectionIndex++; 
      sectionIndex = sectionIndex % sectionList.length; 
    }, 7.5 * 1000);
  }

  if (urlParams.has("username"))
  {
    username = urlParams.get("username");

    getUser(username);

    var choicesInterval = setInterval(function() { getUser(username); }, 5 * 1000);
  }

  populateValueList();
});