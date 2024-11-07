document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('#searchForm');
    const searchInput = document.querySelector('#searchInput');
    const categorySelect = document.querySelector('#categorySelect');
    const servicesList = document.querySelector('#servicesList');
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const searchQuery = searchInput.value;
            const selectedCategory = categorySelect.value;
            
            // Update URL with search parameters
            const params = new URLSearchParams(window.location.search);
            if (searchQuery) params.set('q', searchQuery);
            if (selectedCategory) params.set('category', selectedCategory);
            
            window.location.href = `/services?${params.toString()}`;
        });
    }
});
