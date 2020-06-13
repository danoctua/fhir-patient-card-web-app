window.onload = function () {
    let selectsVersion = document.getElementsByClassName("select-version");
    for (let i = 0; i < selectsVersion.length; i++) {
        console.log(i);
        selectsVersion[i].addEventListener('change', function (e) {
            console.log("changed");
            let selectedVersion = selectsVersion[i].options[selectsVersion[i].selectedIndex].value;
            window.location.href = window.location.href.split('?')[0] + "?version=" + selectedVersion;
        }, false);

    }
}