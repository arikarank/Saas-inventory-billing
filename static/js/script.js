// Global JavaScript functions

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Show loading spinner
function showLoading() {
    $('#loading-spinner').show();
}

function hideLoading() {
    $('#loading-spinner').hide();
}

// Auto-hide alerts after 5 seconds
$(document).ready(function() {
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // Enable tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Enable popovers
    $('[data-bs-toggle="popover"]').popover();
});

// Search functionality
function searchProducts(query) {
    $.getJSON('/api/products/search?q=' + encodeURIComponent(query), function(products) {
        // Update search results
    });
}