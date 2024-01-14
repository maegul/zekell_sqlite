console.log('hello world')


// var count = 0

// var action_but = document.querySelector('#but_fetch')
// var content = document.querySelector('#content')

// console.log('button element?', action_but)

// action_but.addEventListener(
// 	'click',
// 	() => {
// 		count = count + 1
// 		// content.innerHTML = count

// 		fetch("http://0.0.0.0:5000/jsontest")
// 			.then((response) => response.json())
// 			.then((body) => {
// 				console.log(body)
// 				// just add more inner divs?
// 				content.innerHTML = content.innerHTML + '<br>' + count + ': ' + body['content']
// 			}
// 			)
// 			.catch((error) => console.log(error));

// 	}
// )

function update_search_results(data){
	// console.log('search data', data)
	const search_results_div = document.getElementById('search_results_div')
	search_results_div.innerHTML = ""

	for (var i = data.length - 1; i >= 0; i--) {
		// data-* attributes always strings?  In HTML, probably yes!
		const result = `
			<div class="search_result" data-note-id="${data[i]['id']}">
				<p class="search_result_label">${data[i]['title']} (${data[i]['id']})</p>
				<button class="search_result_preview_button">P</button>
			</div>
		`
		search_results_div.insertAdjacentHTML('beforeend', result)
		// const result = document.createElement('p')
		// result.textContent = `${data[i][1]} (${data[i][0]})`
		// result.setAttribute('data-note-id', data[i][0])
		// search_results_div.appendChild(result)
	}

	const preview_buttons = document.querySelectorAll('.search_result_preview_button')
	// const preview_buttons = document.getElementsByClassName('search_result_preview_button')
	console.log(preview_buttons)
	preview_buttons.forEach(
		function (value) {
			value.addEventListener(
				'click',
				function (event) {
					const note_id = value.parentNode.getAttribute('data-note-id')

					const url_params = new URLSearchParams({id: parseInt(note_id)})
					fetch("http://0.0.0.0:5000/note?" + url_params)
					.then(response => response.json())
					.then(data => {
						// Handle the response data and update the page
						console.log(data);
						const preview = document.body.appendChild(document.createElement('div'))
						preview.innerHTML = data['body']
						// CSS for floating preview:
							// position: absolute;
							// top: 20%;
							// background-color: #EEE;
							// height: 50%;
							// width: 50%;
							// margin-left: 15%;
							// overflow: auto;
							// white-space: pre-wrap;
							// overflow: auto;
					})
					.catch(error => {
						console.error("Error:", error);
					});

				}
			)
		}
	)

}

document.getElementById("general_query_form")
	.addEventListener("submit", function (event) {
		event.preventDefault();

		const formData = new FormData(event.target);

		// console.log('form data', formData)

		fetch("http://0.0.0.0:5000/general_search", {
			method: "POST",
			body: formData,
		})
		.then(response => response.json())
		.then(data => {
			// Handle the response data and update the page
			update_search_results(data);
		})
		.catch(error => {
			console.error("Error:", error);
		});
});



// > Encoding queries

// >> Example from GPT

// const query = "this is:; a test";
// const encodedQuery = encodeURIComponent(query);

// const apiUrl = "http://your-api-url/general_search?query=" + encodedQuery;

// // Now, you can use the apiUrl in your AJAX request or wherever you are making the HTTP request.

