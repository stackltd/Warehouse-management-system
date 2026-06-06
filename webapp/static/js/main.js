(function() {

    
    // $("#titles_fields").click(function() { // ID откуда кливаем
    //     $('html, body').animate({
    //     scrollTop: $(".scrollhere").offset().top // класс объекта к которому приезжаем
    //     }, 1000); // Скорость прокрутки
    //    });

    // window.onload = function() { 
    //     $('html, body').animate({
    //        scrollTop: $('.scrollhere').offset().top - 900
    //          }, 2
    //      );
    //   }
 
    // let filter_select = document.querySelector('.scrollhere')
    // filter_select.style.position = "fixed"
    
    window.onload = function() {
        var divs = document.getElementsByTagName("div");
    
        for (var i in divs) {
            if (divs[i].className.indexOf("scrollhere") > -1) {
                //Finds top of of the element
                var top = 0;
                var obj = divs[i];
    
                if (obj.offsetParent) {
                    do {
                        top += obj.offsetTop;
                    } while (obj = obj.offsetParent);
                }
    
                //Scroll to location
                console.log(top)
                // window.scroll(0, top);
                
                if (top > 942 && top < 1300)
                {window.scroll(0, 400);
                    console.log("1")}
                else if (top > 1300 && top < 1500)
                {window.scroll(0, 600);
                    console.log("2")}
                else if (top > 1500)
                {window.scroll(0, top);
                    console.log("3")}
    
                break;
            }
        }
    };

    var popupButtons = document.querySelectorAll(".open-popup")

    var popupContainer = document.querySelector('.popup-container')

    function popup_container_control () {
        popupContainer.style.display = "flex"
    }

    for (let button of popupButtons) {
        button.addEventListener('click', popup_container_control)
      }

      popupContainer.addEventListener('click', function(event){
        if(event.target == popupContainer) {
            popupContainer.style.display = 'none';
            }
        });
    // if (filter_select) {
    //     filter_select.addEventListener('DOMContentLoaded', change_list)
    // }

})()

