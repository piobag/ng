class DataTable {
    constructor({
        name,
        apiEndpoint, // API endpoint URL to fetch data
        perPage = 5, // number of items to show per page
        filter = 'created', // default filter to apply
        headers = ['Column 1', 'Column 2', 'Column 3'], // table header labels
        rowTemplate = (data) => `
            <tr>
                <td>${data.column1}</td>
                <td>${data.column2}</td>
                <td>${data.column3}</td>
            </tr>
        `, // template function to render each table row
        paginationTemplate = (currentPage, totalPages) => {
            // Add pagination CSS
            const styleElem = document.createElement('style');
            styleElem.innerHTML = `
                /* User */

                .pagination_content {
                    display: flex;
                    justify-content: space-around;
                    align-items: center;
                    /* width: 100%; */
                }
                
                .pagination_content .pagination_perpage {
                    display: flex;
                    align-items: center;
                }
                .pagination_content .pagination_perpage > b {
                    margin-right: 1rem;
                }
                
                .pagination_content .pagination_perpage .border-style,
                .pagination_content .pagination_search .border-style {
                    border: 1px solid var(--first-color-dark);
                    padding: 4px 24px 4px 4px;
                    border-radius: 25px;
                    text-align: center;
                }
            `;
            document.head.appendChild(styleElem);
            
            return `
                <div class="pagination_content">
                    <div class="pagination_perpage">
                        <b>{{ _('Per page') }}:</b>
                        <div>
                            <select onchange="${this.name}_change_perpage(this.value)" class="form-select form-select-sm change-pagination border-style per_page">
                            <option value="1" ${this.perPage == 1 ? 'selected' : ''}>1</option>
                            <option value="5" ${this.perPage == 5 ? 'selected' : ''}>5</option>
                            <option value="10" ${this.perPage == 10 ? 'selected' : ''}>10</option>
                            <option value="25" ${this.perPage == 25 ? 'selected' : ''}>25</option>
                            <option value="50" ${this.perPage == 50 ? 'selected' : ''}>50</option>
                            <option value="100" ${this.perPage == 100 ? 'selected' : ''}>100</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="pagination_pages">
                        <nav class="pages">
                        </nav>
                    </div>
                </div>
            `
        },
        spinner = false,
    }) {
        this.name = name;
        this.apiEndpoint = apiEndpoint;
        this.perPage = perPage;
        this.filter = filter;
        this.headers = headers;
        this.rowTemplate = rowTemplate;
        this.paginationTemplate = paginationTemplate;
        this.currentPage = 1;
        this.totalPages = 0;
        this.totalItems = 0;
        this.tableElem = null;
        this.paginationElem = null;
        this.loadingElem = null;
        this.errorElem = null;
        this.searchElem = null;
        this.haveSpinner = spinner;
        this.countSpinner = 0;
        this.loadingHtml = `<i class="fas fa-sm fa-sync"></i>`;
    }

    init(tableElemSelector, paginationElemSelector, loadingElemSelector, errorElemSelector, searchElemSelector) {
        this.tableElem = document.querySelector(tableElemSelector);
        this.paginationElem = document.querySelector(paginationElemSelector);
        this.loadingElem = document.querySelector(loadingElemSelector);
        if (this.haveSpinner) {
            this.loadingElem.innerHTML = this.loadingHtml
        } else {
            this.loadingElem.innerHTML = spinner_b
        }
        this.errorElem = document.querySelector(errorElemSelector);
        this.searchElem = document.querySelector(searchElemSelector);
        this.loadItems();
    }

    async loadItems(args=false) {
        if (this.countSpinner > 0) {
            return
        }
        if (this.haveSpinner) {
            this.countSpinner += 1
            this.loadingElem.innerHTML = spinner_b;
        } else {
            this.loadingElem.style.display = 'block';
            this.tableElem.style.display = 'none';
            this.paginationElem.style.display = 'none';
            this.errorElem.style.display = 'none';
        }
        this.tableElem.innerHTML = '';

        let apiEndpointUrl = `${this.apiEndpoint}?start=${(this.currentPage - 1) * this.perPage}&length=${this.perPage}&filter=${this.filter}${this.searchElem ? `&search=${this.searchElem.value}` : ''}`;
        if (args) apiEndpointUrl += '&'+args;
        fetch(apiEndpointUrl)
            .then(response => response.json())
            .then(data => {
                if (data.result) {
                    this.totalItems = data.total;
                    this.totalPages = Math.ceil(this.totalItems / this.perPage);
                    this.renderTable(data.result);
                    this.renderPagination();
                } else {
                    this.errorElem.innerHTML = `Unknown data: ${JSON.stringify(data)}`;
                    this.errorElem.style.display = 'block';
                }
            })
            .catch(error => {
                this.errorElem.innerHTML = `Error in API: ${error}`;
                this.errorElem.style.display = 'block';
            })
            .finally(() => {
                if (this.haveSpinner) {
                    this.countSpinner -= 1
                    if (this.countSpinner == 0) {
                        this.loadingElem.innerHTML = this.loadingHtml
                    }
                } else {
                    this.loadingElem.style.display = 'none';
                    this.tableElem.style.display = 'block';
                    this.paginationElem.style.display = 'block';
                }
            });
    }
    renderTable(items) {
        const headersHtml = this.headers.map(header => `<th>${header}</th>`).join('');
        const theadHtml = `<thead><tr>${headersHtml}</tr></thead>`;
        const thead = document.createElement('thead');
        thead.innerHTML = theadHtml;
        const rowsHtml = items ? items.map(row => this.rowTemplate(row)).join('') : '';
        const tbodyHtml = `<tbody>${rowsHtml}</tbody>`;
        const tbody = document.createElement('tbody');
        tbody.innerHTML = tbodyHtml;

        let start = (this.currentPage - 1) * this.perPage + 1
        let last_page = start + this.perPage

        const footHtml = `<td colspan="3"><p>${this.totalItems === 0 ? 'Nenhum item encontrado.': `Filtrando de ${start} até ${this.totalItems < last_page ? this.totalItems : last_page} do total de ${this.totalItems} itens.`}<p></td>`
        const tfoot = document.createElement('tfoot');
        tfoot.innerHTML = footHtml;

        this.tableElem.appendChild(thead);
        this.tableElem.appendChild(tbody);
        this.tableElem.appendChild(tfoot);
    }
    renderPagination() {
        const paginationHtml = this.paginationTemplate(this.currentPage, this.totalPages);
        this.paginationElem.innerHTML = paginationHtml;

        const pagesElem = this.paginationElem.querySelector('.pages')
        
        const paginationList = document.createElement('ul');
        paginationList.classList.add('pagination', 'pagination-sm');

        let page = 1
        let pages = Array.from(Array(Math.floor((this.totalItems-1)/this.perPage)+1)).map(p => page++)
        let current_page = Math.floor((this.currentPage - 1) * this.perPage/this.perPage)+1
        if (pages.length > 6 ) {
            if (current_page < 5) {
                pages = [1, 2, 3, 4, 5, '...', pages.length]
            } else if (current_page > pages.length - 4 ) {
                pages = [1, '...', pages.length-4, pages.length-3, pages.length-2, pages.length-1, pages.length]
            } else {
                pages = [1, '...', current_page-2, current_page-1, current_page, current_page+1, current_page+2, '...', pages.length]
            }
        }
        for (let p of pages) {
            let paginationItem = document.createElement('li');
            paginationItem.classList.add('page-item');
            if (this.currentPage === p) {
                paginationItem.classList.add('active');
            }
            let paginationLink = document.createElement('a');
            paginationLink.classList.add('page-link');
            paginationLink.textContent = p;
            if (!isNaN(p)) {
                paginationLink.addEventListener('click', () => {
                    this.currentPage = p;
                    this.loadItems();
                });
            }
            paginationItem.appendChild(paginationLink);
            paginationList.appendChild(paginationItem);
        }

        pagesElem.appendChild(paginationList);

        const prevButton = this.paginationElem.querySelector('.prev');
        const nextButton = this.paginationElem.querySelector('.next');
        if (prevButton) {
            prevButton.addEventListener('click', () => {
                this.currentPage -= 1;
                this.loadItems();
            });
        }
        if (nextButton) {
            nextButton.addEventListener('click', () => {
                this.currentPage += 1;
                this.loadItems();
            });
        }
        // const pageButtons = this.paginationElem.querySelectorAll('button:not(.prev):not(.next)');
        // pageButtons.forEach((button, i) => {
        //     button.addEventListener('click', () => {
        //         this.currentPage = i + 1;
        //         this.loadItems();
        //     });
        // });
    }
}