var uls = document.getElementById("navbar-ul");
var lis = uls.getElementsByTagName("li");

for (var i = 0; i < lis.length; i++){
    lis[i].addEventListener("click", function(){
        var current = document.getElementsByTagName("active");
        current[0].className = current[0].className.replace("active","");
        this.className = 'active';
    });
}