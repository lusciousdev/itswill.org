const data = document.currentScript.dataset;

const lastMsgUrl = data.lastmsgapi;
const fiveRecordUrl = data.fiverecordapi;
const overall = (data.overall == "true");

function prevSlide() 
{
  var index = $(".page.show").index();

  if (index > 0)
  {
    $($(".page")[index]).removeClass("show");
  
    $($(".page")[index - 1]).addClass("show");
  }
}

function nextSlide()
{
  var index = $(".page.show").index();

  if (index < $(".page").length - 1)
  {
    $($(".page")[index]).removeClass("show");
  
    $($(".page")[index + 1]).addClass("show");
  }

}

function handleAjaxError(data)
{
  console.log("~~~~~~~~~~~ERROR~~~~~~~~~~~~~~~~~~~")
  console.log(data);
}

function handleLastMessage(data)
{
  if (overall)
  {
    $("#last-msg").html("The last message of the year was \"{0}\" sent by {1}".format(escapeHtml(data["message"]), escapeHtml(data["commenter"])));
  }
  else
  {
    $("#")
    $("#last-msg").html("Your last message of the year was \"{0}\" sent on {1}".format(escapeHtml(data["message"]), escapeHtml(data["prettytime"])));
  }
}

function getLastMessage()
{
  AjaxGet(lastMsgUrl, {}, handleLastMessage, handleAjaxError);
}

function handleFiveRecord(data)
{
  ontimePerc = data["on-time"] / data["total"];
  earlyPerc = data["early"] / data["total"];
  latePerc = 1 - ontimePerc - earlyPerc;

  if ($("#five-record").length != 0)
  {
    $("#early").html("Will went live early <b>{0}</b> times ({1} of streams)".format(data["early"], earlyPerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#on-time").html("He went live on time <b>{0}</b> times ({1} of streams)".format(data["on-time"], ontimePerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#late").html("He was late for <b>{0}</b> streams ({1} of streams)".format(data["total"] - data["early"] - data["on-time"], latePerc.toLocaleString(undefined, {style: "percent", maximumFractionDigits: 1})));
    $("#total-streams").html("That puts us at <b>{0}</b> days streamed in 2024".format(data["total"]));
  }
}

function getFiveRecord()
{
  AjaxGet(fiveRecordUrl, {}, handleFiveRecord, handleAjaxError);
}

$(window).on('load', function() {
  getLastMessage();
  getFiveRecord();

  var lastMsgInterval = setInterval(getLastMessage, 5000);
  if ($("#five-record").length != 0)
  {
    var fiveRecordInterval = setInterval(getFiveRecord, 15000);
  }
});