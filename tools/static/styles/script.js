function startLoading() {
    var loading = setInterval(loadMacs, 1000);
}

function loadMacs() {
    fetch('/loadmacs', {method : 'GET'})
    .then(res => {
        return res.json();
    })
    .then(data => {
        if (data.entries) {
            all_entries = data.entries;
            main_div = document.getElementById('select-field');
            main_div.innerHTML = '';
            for (let i in all_entries){
                selectable = document.createElement('button');
                selectable.textContent = all_entries[i]['mac'];
                selectable.setAttribute('class', 'selectable-button');
                if (all_entries[i]['selected']){
                    selectable.setAttribute('id', 'mac-selected');
                }
                else {
                    selectable.setAttribute('id', 'mac-unselected');
                }
                main_div.appendChild(selectable);
            }
        }
    })
    .catch(err => {
        clearInterval(loadingMacs);
        console.log('Closed the server...');
    })
}

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

function getToken(name) {
    var tokenValue = null;
    if (document.cookie && document.cookie !== ''){
        var cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            var currentCookie = cookies[i].trim();
            if (currentCookie.substring(0, name.length + 1) == (name + '=')){
                tokenValue = decodeURIComponent(currentCookie.substring(name.length + 1));
                break;
            }
        }
    }
    return tokenValue;
}
function macaddListeners() {
    document.querySelectorAll('.selectable-button').forEach(button => {

            addedButtons.push(button);
            button.addEventListener('click', function() {
                var potential_mac = this.textContent;
                console.log(potential_mac);
                var selectedValue = this.getAttribute('id');
                console.log('what');

                if (selectedValue == 'mac-unselected'){
                    var postData = {
                        mac_address : potential_mac,
                        selected : true
                    }
                } else {
                    var postData = {
                        mac_address : potential_mac,
                        selected : false
                    }
                }

                fetch('/managemac/', {method : 'POST', 
                    headers : {
                        'Content-Type' : 'application/json',
                        'X-CSRFToken' : getToken('csrftoken')
                    },
                    body : JSON.stringify(postData)
                })
                .finally(() => {
                    loadMacs();
                })
            });
        
    });
    }

var addedButtons = [];
var btn = document.getElementById("auto-fill");
var storeLocally = document.getElementById('id_save_locally');
var snifferButton = document.getElementById('begin'); 
const loadPackets = setInterval(load_packets, 1000);
const loadingMacs = setInterval(loadMacs, 1000);
const addListeners = setInterval(macaddListeners, 1001)
btn.addEventListener("click", auto_fill);
storeLocally.addEventListener('change', enable_storage);