
function $(query) {
  return document.querySelector(query);
}

let all_files = []
let entry_name = ""

window.onload = () => {
    $('#file_select').onclick = function () {
        $('#file_input').click()
    }

    $("#file_input").addEventListener("change", function(evnt) {
        event.preventDefault()
        const new_file = $('#file_input').files[0]
        $('#file_input').value = ""

        for (let file in all_files) {
            if (file.name == new_file.name) {
                alert("File already added!")
                return
            }
        }

        if (all_files.length == 0) {
          entry_name = new_file.name.split(".")[0]
        } else {
            if (new_file.name.split(".")[0] != entry_name) {
                alert("File prefixes need to be identical!")
                return
            }
        }

        all_files.push(new_file)

        const p = document.createElement('p')
        const button = document.createElement('button')
        p.innerText = new_file.name
        button.innerText = "Remove"
        button.setAttribute("name", new_file.name)
        button.onclick = function (e) {
            const name = e.target.getAttribute("name")
            all_files.splice(all_files.indexOf(name), 1);
            e.target.parentNode.remove()
        }
        p.appendChild(button)
        $("#file_list").appendChild(p)
  }, false)

  function clear() {
    $("#tags").value = ""
    $("#title").value = ""
    $("#author").value = ""
    $("#notes").value = ""
    $("#license").value = ""
    $("#language").value = ""

    entry_name = ""
    all_files = []
    $("#file_list").innerHTML = ""
  } 

  $('#submit').onclick = function (evnt) {
    evnt.preventDefault()

    if (entry_name.length == 0) {
      alert("Ha, nothing to submit!")
      return
    }

    let formData = new FormData()
    let request = new XMLHttpRequest()

    request.onreadystatechange = function() {
        if (4 !== this.readyState) {
            // not yet ready
            return;
        }

        if (200 === this.status) {
            alert('Success - thank you for the treat!')
        } else {
            console.log("some error occured: " + this.status)
        }
    }

    formData.set('name', entry_name)
    formData.set('tags', $("#tags").value)
    formData.set('title', $("#title").value)
    formData.set('author', $("#author").value)
    formData.set('notes', $("#notes").value)
    formData.set('license', $("#license").value)
    formData.set('language', $("#language").value)

    for (let file of all_files) {
        formData.append("files[]", file)
    }
    
    request.open("POST", 'http://localhost:8000/send')
    request.send(formData)
  }
};
