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

function setStat(statid, list)
{
  list.forEach((item) => {
    $("#{0}-leaderboard".format(statid)).append("<li class='leaderboard-item'>{0} - {1}</li>".format(item[0],  new Intl.NumberFormat().format(item[1])))
  });
}

function handleGetLeaderboardResponse(category, text)
{
  var respJson = JSON.parse(text);

  setStat(category, respJson)
}

function handleGetLeaderboardError(text)
{
  console.log("API Error: " + text);
}

function getCategory(category, htmlCategory)
{
  var reqUrl = apiUrl + "/api/v1/leaderboard?category=" + encodeURIComponent(category);
  xmlHttpRequestAsync("GET", reqUrl, (text) => { handleGetLeaderboardResponse(htmlCategory, text); }, handleGetLeaderboardError);
}

$(window).on('load', function () {
  getCategory("messages", "msg-count");
  getCategory("clips", "clip-count");
  getCategory("views", "clip-views");
  getCategory("ITSWILL7", "itswill7");
  getCategory("POUND", "itswillPound");
  getCategory("STSMG", "stsmg");
  getCategory("KSMG", "ksmg");
  getCategory("ETSMG", "etsmg");
  getCategory("SNEAK", "itswillSneak");
  getCategory("SIT", "itswillSit");
  getCategory("LOVE", "itswillL");
  getCategory("POG", "pog");
  getCategory("DANKIES", "dankies");
  getCategory("SHOOP", "shoop");
  getCategory("POGO", "pogo");
  getCategory("MONKA", "monka");
  getCategory("GASP", "gasp");
  getCategory("MMYLC", "mmylc");
  getCategory("DANCE", "dance");
  getCategory("VVKOOL", "vvkool");
  getCategory("SPIN", "spin");
  getCategory("CHICKEN", "chicken");
  getCategory("GIGGLE", "giggle");
  getCategory("LUL", "lul");
  getCategory("SONIC", "sonic");
  getCategory("CUM", "cum");
});