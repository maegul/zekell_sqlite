console.log('hello world')

const base_url = "http://0.0.0.0:5000"

// > Utils

function removeAllChildNodes(node) {
	while (node.firstChild) {
		node.removeChild(node.firstChild)
	}
}

// > Template functions

function update_note_view(note_data) {
	const note_view = document.getElementById('zkl_note_view')

	const title = note_view.querySelector(".note_view_title")
	const body = note_view.querySelector(".note_view_body")
	removeAllChildNodes(title)
	// removeAllChildNodes(body)
	body.value = ""

	title.textContent = note_data['title']
	// body.textContent = note_data['body']
	body.value = note_data['body']
}

function add_preview_event_listener(button, note_id){

	button.addEventListener(
		'click',
		function (event) {
			// const note_id = value.parentNode.getAttribute('data-note-id')

			const url_params = new URLSearchParams({id: parseInt(note_id)})
			fetch(`${base_url}/note?` + url_params)
			.then(response => response.json())
			.then(data => {
				// Handle the response data and update the page
				update_note_view(data)
			})
			.catch(error => {
				console.error("Error:", error);
			});
		}
	)

}

function add_explore_event_listener(button, note_id, direction){

	// direction should be either "children" or "parents"
	// default to 'children' if falsy
	direction = direction || 'children'

	button.addEventListener(
		'click',
		function (event) {
			console.log(`Explore ${note_id}`)
			console.log(event)

			const data = {
				query: `id: ${note_id}; ${direction}`,
				// query: `id: ${note_id}; children`,
			}

			fetch(
				`${base_url}/general_search`,
				{
					method: "POST",
					body: JSON.stringify(data),
					headers: {
						'Content-Type': 'application/json'
					}
				})
			.then(response => response.json())
			.then(data => {
				// Handle the response data and update the page
				console.log(data, direction)
				// direction here is enclosed from above
				update_search_results(data, event.target.parentElement, direction);
			})
			.catch(error => {
				console.error("Error:", error);
			});
		}
	)

}

function set_result_row_data(element, data) {

	element.setAttribute('data-note-id', data['id'])
	element.setAttribute('data-note-title', data['title'])

	return element
}

function get_result_row_data(element) {


	const data = {
		id: element.getAttribute('data-note-id'),
		title: element.getAttribute('data-note-title')
	}

	return data
}

function make_result_row(data, is_explore_source) {

	const template = document.querySelector('#zkl_template_result_row')

	const result = template.content.cloneNode(true)
	const result_cont = result.querySelector('div')
	const result_text = result.querySelector('p')

	set_result_row_data(result_cont, data)

	result_text.textContent = `${data['title']}`
	// result_text.textContent = `${data['title']} (${data['id']})`

	const result_parents_button = result.querySelector('.search_result_parents_button')
	const result_children_button = result.querySelector('.search_result_children_button')
	const result_preview_button = result.querySelector('.search_result_preview_button')

	add_explore_event_listener(result_parents_button, data['id'], 'parents')
	add_explore_event_listener(result_children_button, data['id'], 'children')
	add_preview_event_listener(result_preview_button, data['id'])

	if (is_explore_source) {

		result_cont.classList.add("explore_source_note")
	}

	return result
}


// > Main

// >> Search Pane visibility

const search_pane_button = document.getElementById('zkl_search_pane_tab')
search_pane_button.addEventListener("click", function (event) {
	const search_pane_main = document.getElementById('zkl_search_pane')
	const note_view_pane = document.getElementById('zkl_note_view')
	const visibility = search_pane_main.style.visibility

	console.log('search pane button', visibility)

	if (visibility != "hidden") {
		search_pane_main.setAttribute('zkl-initial-width', search_pane_main.style.width)
		search_pane_main.style.width = "0px";
		search_pane_main.style.visibility = "hidden";
		// adjust flex flow of note view pannel
		note_view_pane.setAttribute(
			'zkl-initial-justifyContent', note_view_pane.style.justifyContent)
		note_view_pane.style.justifyContent = "space-around"
	} else {
		search_pane_main.style.width = search_pane_main.getAttribute('zkl-initial-width');
		search_pane_main.style.visibility = "";

		note_view_pane.style.justifyContent = note_view_pane.getAttribute('zkl-initial-justifyContent')
	}

})


// >> Search Results

function update_search_results(data, explore_source, explore_type){
	// console.log('search data', data)
	const search_results_div = document.getElementById('zkl_search_results_div')
	removeAllChildNodes(search_results_div)

	// for displaying the source of an explore action
	console.log('explore', explore_source)

	if (explore_source) {
		source_note_data = get_result_row_data(explore_source)
		const source_note_row = make_result_row(source_note_data, 'explore_source')
		// source_note_row.querySelector('.search_result').classList.add("explore_source_note")
		const source_separator = document.createElement('hr')

		search_results_div.appendChild(source_note_row)
		search_results_div.appendChild(source_separator)

		// Display the direction of the "exploration"
		if (explore_type == "parents" || explore_type == "children") {

			const template = document.querySelector(
				'#zkl_template_explore_results_direction_indicator')

			const direction_indicator = template.content.cloneNode(true)
			const indicator = direction_indicator.querySelector('.explore_results_indicator')
			const indicator_text = (explore_type == "children") ? "V" : "^"
			indicator.textContent = indicator_text

			search_results_div.appendChild(direction_indicator)
		}
	}

	for (var i = data.length - 1; i >= 0; i--) {

		let result_data = data[i]
		const result_row = make_result_row(result_data)
		search_results_div.appendChild(result_row)
	}

}

document.getElementById("zkl_general_query_form")
	.addEventListener("submit", function (event) {
		event.preventDefault();

		const formData = new FormData(event.target);

		console.log('form data', formData)

		fetch(`${base_url}/general_search`, {
			method: "POST",
			body: formData,
			// headers: {}  // No need as set automatically by browswer (multipart/form-data)
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

