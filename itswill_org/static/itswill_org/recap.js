const scriptData = document.currentScript.dataset;

const recapYear = scriptData.year;
const recapMonth = scriptData.month;

const overallRecap = scriptData.overallrecap;
const recapApiURL = scriptData.getrecapdataurl;

var g_ExpandedStat = undefined;

var g_Websocket;
var g_ReconnectInterval = undefined;

function timeToPrettyString(timeInt, abbreviate = false) {
  var days = Math.floor(timeInt / (3600 * 24));
  var rem = timeInt % (3600 * 24);

  var hours = Math.floor(rem / 3600);
  var rem = rem % 3600;

  var minutes = Math.floor(rem / 60);
  var rem = rem % 60;

  var seconds = rem;

  var output = "";

  var msd_hit = false;
  if (days > 0) {
    if (abbreviate) output += days.toLocaleString() + "d ";
    else output += days.toLocaleString() + " days, ";

    msd_hit = true;
  }

  if (msd_hit || hours > 0) {
    if (abbreviate) output += hours.toLocaleString() + "h ";
    else output += hours.toLocaleString() + " hours, ";

    msd_hit = true;
  }

  if (msd_hit || minutes > 0) {
    if (abbreviate)
      output +=
        minutes.toLocaleString() + "m " + seconds.toLocaleString() + "s";
    else
      output +=
        minutes.toLocaleString() +
        " minutes and " +
        seconds.toLocaleString() +
        " seconds";

    msd_hit = true;
  }

  if (!msd_hit) {
    if (abbreviate) output += seconds.toLocaleString() + "s";
    else output += seconds.toLocaleString() + " seconds";
  }

  return output;
}

function handleWebsocketMessage(e) {
  var eventData = JSON.parse(e.data);

  $("#msg-count-value").html(eventData["count_messages"].toLocaleString());
  $("#char-count-value").html(eventData["count_characters"].toLocaleString());
  $("#char-time-value").html(
    timeToPrettyString(Math.floor(eventData["count_characters"] / 5), true),
  );

  if (eventData["last_message"] !== null) {
    $(".last_message").html(eventData["last_message"]["message"]);
    $(".last_chatter").html(
      eventData["last_message"]["commenter"]["display_name"],
    );
  } else {
    $(".last_message").html("NO LAST MESSAGE");
    $(".last_chatter").html("NO ONE");
  }
  
  if (eventData["last_message"] !== null) {
    var msg = '"' + eventData["last_message"]["message"] + '"';
    if (overallRecap == "1") {
      msg += " - " + eventData["last_message"]["commenter"]["display_name"];
    }
    $("#last-msg-value").html(msg);
  } else {
    $("#last-msg-value").html("<i>None</i>");
  }

  for (const [key, val] of Object.entries(eventData["counters"])) {
    $("#" + key + "-value").html(val["total"].toLocaleString());

    for (const [fragKey, fragVal] of Object.entries(val["members"])) {
      cleanKey = fragKey.replace("+", "\\+");
      $("#" + cleanKey + "-value").html(fragVal.toLocaleString());
    }
  }
}

function attemptWebsocketReconnect(e) {
  if (g_ReconnectInterval == undefined) {
    g_ReconnectInterval = setInterval(() => {
      if (g_Websocket.readyState == WebSocket.OPEN) {
        console.log("Reconnected websocket.");
        clearInterval(g_ReconnectInterval);
        g_ReconnectInterval = undefined;
        return;
      }

      console.log("Attempting to reconnect websocket.");
      connectWebsocket();
    }, 5000);
  }
}

function connectWebsocket() {
  var protocol = "ws:";
  if (window.location.protocol == "https:") protocol = "wss:";

  var wsUrl = "{0}//{1}/ws/recap/".format(protocol, window.location.host);
  if (parseInt(recapYear) > 0)
  { 
    wsUrl = "{0}{1}/".format(wsUrl, recapYear);
    if (parseInt(recapMonth) > 0)
      wsUrl = "{0}{1}/".format(wsUrl, recapMonth);
  }
  g_Websocket = new WebSocket(wsUrl);

  g_Websocket.onopen = (e) => {};
  g_Websocket.onmessage = (e) => {
    handleWebsocketMessage(e);
  };
  g_Websocket.onclose = (e) => {
    attemptWebsocketReconnect(e);
  };
}

function handleRecapData(respData) {
  $("#msg-count-value").html(respData["count_messages"].toLocaleString());
  $("#char-count-value").html(respData["count_characters"].toLocaleString());
  $("#char-time-value").html(
    timeToPrettyString(Math.floor(respData["count_characters"] / 5), true),
  );
  $("#clip-count-value").html(respData["count_clips"].toLocaleString());
  $("#clip-views-value").html(respData["count_clip_views"].toLocaleString());
  $("#clip-watch-value").html(
    timeToPrettyString(respData["count_clip_watch"], true),
  );

  if (respData["first_message"] !== null) {
    var msg = '"' + respData["first_message"]["message"] + '"';
    if (overallRecap == "1") {
      msg += " - " + respData["first_message"]["commenter"]["display_name"];
    }
    $("#first-msg-value").html(msg);
  } else {
    $("#first-msg-value").html("<i>None</i>");
  }

  if (respData["last_message"] !== null) {
    var msg = '"' + respData["last_message"]["message"] + '"';
    if (overallRecap == "1") {
      msg += " - " + respData["last_message"]["commenter"]["display_name"];
    }
    $("#last-msg-value").html(msg);
  } else {
    $("#last-msg-value").html("<i>None</i>");
  }

  for (const [key, val] of Object.entries(respData["counters"])) {
    $("#" + key + "-value").html(val["total"].toLocaleString());

    for (const [fragKey, fragVal] of Object.entries(val["members"])) {
      cleanKey = fragKey.replace("+", "\\+");
      $("#" + cleanKey + "-value").html(fragVal.toLocaleString());
    }
  }
}

function handleAjaxError(data) {
  console.log("~~~~~~~~~~~ERROR~~~~~~~~~~~~~~~~~~~");
  console.log(data);
}

function requestRecapData() {
  AjaxGet(recapApiURL, {}, handleRecapData, handleAjaxError);
}

$(window).on("load", function () {
  $(".expand-stat").click(function (ev) {
    var targetId = $(ev.currentTarget).attr("group");

    $("#" + g_ExpandedStat + "-breakdown").css({ "max-height": "0px" });

    if (g_ExpandedStat != targetId) {
      var breakdownId = "#" + targetId + "-breakdown";
      var height = $(breakdownId).find(".stat-breakdown-table").height() + 18;
      $(breakdownId).css({ "max-height": String(height) + "px" });
      g_ExpandedStat = targetId;
    } else {
      g_ExpandedStat = undefined;
    }
  });

  if (overallRecap == "1")
    connectWebsocket();

  requestRecapData();
  setInterval(requestRecapData, 10000);
});
