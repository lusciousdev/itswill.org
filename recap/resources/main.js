var apiUrl = "https://recap.itswill.org"

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

function setStat(statid, statvalue)
{
  $("#{0}-value".format(statid)).html(statvalue)
}

function handleGetUserResponse(text)
{
  var respJson = JSON.parse(text);

  if (respJson["userid"] == -1)
  {
    $("#stat-title").html("Overall statistics for 2023");
    $("#first-msg").hide();
  }
  else
  {
    $("#stat-title").html("{0}'s statistics for 2023".format(respJson["display_name"]));
  }

  setStat("msg-count",    new Intl.NumberFormat().format(respJson["total_messages"]));
  setStat("clip-count",   new Intl.NumberFormat().format(respJson["total_clips"]));
  setStat("clip-views",   new Intl.NumberFormat().format(respJson["clip_views"]));
  setStat("first-msg",    "\"{0}\"".format(respJson["first_message"]));
  setStat("itswill7",     new Intl.NumberFormat().format(respJson["itswill7"]));
  setStat("itswillPound", new Intl.NumberFormat().format(respJson["itswillPound"]));
  setStat("etsmg",        new Intl.NumberFormat().format(respJson["itswillEndTheStreamMyGuy"]));
  setStat("ksmg",         new Intl.NumberFormat().format(respJson["itswillKeepStreamingMyGuy"]));
  setStat("itswillSneak", new Intl.NumberFormat().format(respJson["itswillSneak"]));
  setStat("itswillSit",   new Intl.NumberFormat().format(respJson["itswillSit"]));
  setStat("itswillL",     new Intl.NumberFormat().format(respJson["itswillL"]));
  setStat("pog",          new Intl.NumberFormat().format(respJson["Pog"]));
  setStat("shoop",        new Intl.NumberFormat().format(respJson["ShoopDaWhoop"]));
  setStat("mmylc",        new Intl.NumberFormat().format(respJson["MusicMakeYouLoseControl"]));
  setStat("giggle",       new Intl.NumberFormat().format(respJson["x0r6ztGiggle"]));
  setStat("vvkool",       new Intl.NumberFormat().format(respJson["VVKool"]));
  setStat("gasp",         new Intl.NumberFormat().format(respJson["GASP"]));
  setStat("monka",        new Intl.NumberFormat().format(respJson["monkaS"]));
  setStat("pogo",         new Intl.NumberFormat().format(respJson["PogO"]));
  setStat("spin",         new Intl.NumberFormat().format(respJson["spin"]));
  setStat("cum",          new Intl.NumberFormat().format(respJson["cum"]));
  setStat("chicken",      new Intl.NumberFormat().format(respJson["chicken"]));
  setStat("sonic",        new Intl.NumberFormat().format(respJson["sonic"]));
  setStat("lul",          new Intl.NumberFormat().format(respJson["lul"]));
  setStat("stsmg",        new Intl.NumberFormat().format(respJson["stsmg"]));
  setStat("dance",        new Intl.NumberFormat().format(respJson["dance"]));
  setStat("dankies",        new Intl.NumberFormat().format(respJson["dankies"]));
}

function handleGetUserError(text)
{
  console.log("API Error: " + text);
}

function getUser(username)
{
  var reqUrl = apiUrl + "/api/v1/get?username=" + encodeURIComponent(username);
  xmlHttpRequestAsync("GET", reqUrl, handleGetUserResponse, handleGetUserError);
}

function getOverall()
{
  var reqUrl = apiUrl + "/api/v1/get"
  xmlHttpRequestAsync("GET", reqUrl, handleGetUserResponse, handleGetUserError);
}

$(window).on('load', function () {
  var queryString = window.location.search;
  var urlParams = new URLSearchParams(queryString);

  if (urlParams.has("username"))
  {
    username = urlParams.get("username");

    if (username == "")
    {
      getOverall();
    }
    else
    {
      $("input[name='username']").val(username);
      getUser(username);
    }
  }
  else
  {
    getOverall();
  }

});