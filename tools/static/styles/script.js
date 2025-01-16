function auto_fill() {
    fetch("/update", {method : "GET"})
    .then(res => {
        return res.json();
    })
    .then(data => {
        console.log(data);
        document.getElementById("id_network_interface").value = data.interface_name;
    })
    .catch(err => console.log(err))
}

var btn = document.getElementById("auto-fill");
btn.addEventListener("click", auto_fill);
