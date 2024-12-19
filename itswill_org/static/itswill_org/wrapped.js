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