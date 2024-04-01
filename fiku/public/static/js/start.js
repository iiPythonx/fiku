const escape = (t) => t.split("'").join("\\'").split("\"").join("\\\"");
const show_stat = async (type, timespan) => {
    const stat = document.querySelectorAll(`section[data-item-type = "${type}"] > span[data-timespan = "${timespan}"]`)[0];
    for (const other_stat of document.querySelectorAll(`section[data-item-type = "${type}"] span`)) other_stat.style.opacity = "1";
    stat.style.opacity = "0.5";

    // Handle pulse
    if (type === "pulse") {
        const table = stat.parentElement.getElementsByTagName("table")[0];
        table.innerHTML = "";

        // Make request
        const resp = await (await fetch(`/api/pulse?timespan=${timespan}`)).json();
        const max_value = Math.max(...resp.data.map((x) => x.value));
        for (let obj of resp.data) {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class = "timerange">${obj.title}</td>
                <td class = "amount">
                    <a href = "/scrobbles?in=2024/3/21">${obj.value}</a>
                </td>
                <td class = "bar">
                    <a href = "/scrobbles?in=2024/3/21"><div style = "width: ${(obj.value / max_value) * 100}%;"></div></a>
                </td>
            `;
            table.appendChild(row);
        }
        return;
    }

    // Load tiles
    const tiles = stat.parentElement.getElementsByTagName("div")[0];
    tiles.innerHTML = "";

    // Make request
    const resp = await (await fetch(`/api/top_items?item_type=${type}&timespan=${timespan}`)).json();
    for (let i = 0; i < resp.data.length; i++) {
        let query = `artist=${escape(resp.data[i].artist)}`;
        if (type !== "artist") query += `&${type}=${escape(resp.data[i][type])}`;

        // Create actual tile
        const tile = document.createElement("div");
        tile.classList.add("tile");
        tile.innerHTML = `
            <a href = "/${type}?${query}">
                <div class = "lazy entered loaded" style = "background-image: url('/image?${query}');">
                    <span class = "stats">#${i + 1}</span>
                    <span>${resp.data[i][type]}</span> 
                </div>
            </a>
        `;
        tiles.appendChild(tile);
    }
};

let lastType = null;
for (const stat of document.getElementsByClassName("stat-select")) {
    const itemType = stat.parentElement.getAttribute("data-item-type");
    stat.addEventListener("click", async (e) => {
        await show_stat(itemType, stat.getAttribute("data-timespan"));
    });
    if (itemType !== lastType) {
        show_stat(itemType, "month");
        lastType = itemType;
    }
}