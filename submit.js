
const remote_url = "//mwarning.de:4223/submit"
let all_files = {}
let entry_name = ""


function $(query) {
  return document.querySelector(query);
}

// ignores duplicate parameters
function getGetParameters() {
  var result = {}
  for (const item of location.search.substr(1).split("&")) {
    const tmp = item.split("=")
    result[decodeURIComponent(tmp[0])] = decodeURIComponent(tmp[1] || "")
  }
  return result
}

window.onload = () => {
  const params = getGetParameters()

  entry_name = params["name"] || ""

  if (entry_name.length > 0) {
    $('#header').innerText = "Edit Existing Entry: " + entry_name
  } else {
    $('#header').innerText = "Submit A New Sticker!"
  }

  $("#tags").value = params["tags"] || ""
  $("#title").value = params["title"] || ""
  $("#author").value = params["author"] || ""
  $("#notes").value = params["notes"] || ""
  $("#link").value = params["link"] || ""
  $("#license").value = params["license"] || ""
  $("#language").value = params["language"] || ""

  $('#file_select').onclick = function () {
    $('#file_input').click()
  }

  $("#file_input").addEventListener("change", function(evnt) {
    event.preventDefault()
    const new_file = $('#file_input').files[0]
    $('#file_input').value = ""

    for (let name in all_files) {
      if (name == new_file.name) {
        alert("File already added!")
        return
      }
    }

    if (entry_name.length == 0) {
      entry_name = new_file.name.split(".")[0]
    } else {
      if (new_file.name.split(".")[0] != entry_name) {
        alert("File names need to identical before the first dot in the name!")
        return
      }
    }

    if (!/^[0-9a-zA-Z_.-]{3,32}$/.test(new_file.name)) {
      alert("File name has invalid characters or is not 3-64 characters long.");
      return;
    }

    all_files[new_file.name] = new_file

    const p = document.createElement('p')
    p.innerText = new_file.name

    const button = document.createElement('button')
    button.innerText = "Remove"
    button.setAttribute("name", new_file.name)
    button.onclick = function (e) {
      const name = e.target.getAttribute("name")
      delete all_files[name]
      e.target.parentNode.remove()
    }

    const div = document.createElement('div')
    div.appendChild(p)
    div.appendChild(button)
    $("#file_list").appendChild(div)
  }, false)

  function clear() {
    entry_name = ""
    all_files = {}
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
        alert(this.responseText)
      } else {
        alert("Error:" + request.statusText)
      }
    }

    formData.set('name', entry_name)
    formData.set('tags', $("#tags").value)
    formData.set('title', $("#title").value)
    formData.set('author', $("#author").value)
    formData.set('notes', $("#notes").value)
    formData.set('license', $("#license").value)
    formData.set('language', $("#language").value)

    for (let name in all_files) {
      formData.append("files[]", all_files[name])
    }

    request.open("POST", remote_url)
    request.send(formData)
  }
};
