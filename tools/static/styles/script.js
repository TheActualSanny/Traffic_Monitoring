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

function enable_storage() {
    if (document.getElementById('id_save_locally').checked){
        document.getElementById('id_traffic_directory').disabled = false;
    }
    else {
        document.getElementById('id_traffic_directory').disabled = true;
    }
}

function load_packets() {
   fetch("/packets", {method : 'GET'})
   .then(res => {
    return res.json();
   }).then(a => {
    if (a.packets) {
        arr = a.packets;
        console.log(arr);
        mainDiv = document.getElementById('packet-list');
        for(let i = 0; i < arr.length; i++){
                packetData = document.createElement('p');
                packetData.textContent = `Packet SRC IP: ${arr[i].src_ip}\n DST IP: ${arr[i].dst_ip}`;
                console.log(packetData.textContent);
                packetInstance = document.createElement('div');
                packetInstance.setAttribute('id', 'packet-instance');
                packetInstance.appendChild(packetData);
                mainDiv.appendChild(packetInstance);
        }
    }
    }
    ).catch(err => {
        clearInterval(loadPackets);
        console.log('Closed the server...');
    })
}

var btn = document.getElementById("auto-fill");
var storeLocally = document.getElementById('id_save_locally');
const loadPackets = setInterval(load_packets, 2000);
btn.addEventListener("click", auto_fill);
storeLocally.addEventListener('change', enable_storage);