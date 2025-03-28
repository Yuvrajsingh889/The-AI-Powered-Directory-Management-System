// Visualization JavaScript for the AI Directory Manager application

// Function to initialize all visualizations
function initializeVisualizations(visualizationData) {
    if (!visualizationData) {
        console.error('No visualization data available');
        return;
    }
    
    // Initialize each visualization
    createCategoryPieChart(visualizationData.category_distribution);
    createExtensionBarChart(visualizationData.extension_distribution);
    createSizeDistributionChart(visualizationData.size_distribution);
    createDirectoryTreemap(visualizationData.directory_tree);
    createTimeDistributionChart(visualizationData.time_distribution);
}

// Function to create category distribution pie chart
function createCategoryPieChart(data) {
    if (!data || !data.labels || !data.counts) {
        console.error('Invalid category distribution data');
        return;
    }
    
    const ctx = document.getElementById('category-chart');
    if (!ctx) return;
    
    // Generate random colors for pie chart segments
    const colors = generateChartColors(data.labels.length);
    
    // Create pie chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.counts,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'white'
                    }
                },
                title: {
                    display: true,
                    text: 'Files by Category',
                    color: 'white',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const percentage = Math.round((value / data.total_files) * 100);
                            return `${label}: ${value} files (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Function to create extension distribution bar chart
function createExtensionBarChart(data) {
    if (!data || !data.labels || !data.counts) {
        console.error('Invalid extension distribution data');
        return;
    }
    
    const ctx = document.getElementById('extension-chart');
    if (!ctx) return;
    
    // Generate random colors for bar chart
    const colors = generateChartColors(data.labels.length);
    
    // Create bar chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Number of Files',
                data: data.counts,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Top 10 File Extensions',
                    color: 'white',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// Function to create size distribution histogram
function createSizeDistributionChart(data) {
    if (!data || !data.labels || !data.counts) {
        console.error('Invalid size distribution data');
        return;
    }
    
    const ctx = document.getElementById('size-chart');
    if (!ctx) return;
    
    // Create histogram
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Number of Files',
                data: data.counts,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'File Size Distribution',
                    color: 'white',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'File Size',
                        color: 'white'
                    },
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Files',
                        color: 'white'
                    },
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// Function to create directory treemap
function createDirectoryTreemap(data) {
    if (!data) {
        console.error('Invalid directory tree data');
        return;
    }
    
    const container = document.getElementById('directory-treemap');
    if (!container) return;
    
    // Clear any previous charts
    container.innerHTML = '';
    
    // Prepare data for D3.js treemap
    const root = d3.hierarchy(data)
        .sum(d => d.size || 0)
        .sort((a, b) => b.value - a.value);
    
    // Create treemap layout
    const treemapLayout = d3.treemap()
        .size([container.clientWidth, 400])
        .paddingOuter(10)
        .paddingTop(20)
        .paddingInner(2)
        .round(true);
    
    treemapLayout(root);
    
    // Create SVG element
    const svg = d3.select(container)
        .append('svg')
        .attr('width', container.clientWidth)
        .attr('height', 400)
        .attr('viewBox', `0 0 ${container.clientWidth} 400`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Generate color scale based on categories
    const allCategories = [...new Set(
        root.descendants()
            .filter(d => d.data.category)
            .map(d => d.data.category)
    )];
    
    const colorScale = d3.scaleOrdinal()
        .domain(allCategories)
        .range(generateChartColors(allCategories.length));
    
    // Create cells for each node
    const cell = svg.selectAll('g')
        .data(root.descendants())
        .join('g')
        .attr('transform', d => `translate(${d.x0},${d.y0})`);
    
    // Add rectangles for each cell
    cell.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => d.data.category ? colorScale(d.data.category) : '#ccc')
        .attr('stroke', '#fff')
        .attr('opacity', 0.8);
    
    // Add text labels
    cell.append('text')
        .attr('x', 3)
        .attr('y', 15)
        .attr('fill', 'white')
        .text(d => d.data.name)
        .attr('font-size', d => {
            // Scale font size based on rectangle size
            const width = d.x1 - d.x0;
            const height = d.y1 - d.y0;
            const area = width * height;
            return Math.min(14, Math.max(8, area / 3000)) + 'px';
        })
        .attr('opacity', d => {
            // Hide text if cell is too small
            const width = d.x1 - d.x0;
            const height = d.y1 - d.y0;
            return (width > 30 && height > 20) ? 1 : 0;
        });
    
    // Add legend
    const legend = svg.append('g')
        .attr('transform', `translate(10, ${400 - 20 - (allCategories.length * 15)})`);
    
    allCategories.forEach((category, i) => {
        const legendItem = legend.append('g')
            .attr('transform', `translate(0, ${i * 15})`);
        
        legendItem.append('rect')
            .attr('width', 10)
            .attr('height', 10)
            .attr('fill', colorScale(category));
        
        legendItem.append('text')
            .attr('x', 15)
            .attr('y', 9)
            .attr('fill', 'white')
            .attr('font-size', '10px')
            .text(category);
    });
}

// Function to create time distribution line chart
function createTimeDistributionChart(data) {
    if (!data || !data.labels || !data.counts) {
        console.error('Invalid time distribution data');
        return;
    }
    
    const ctx = document.getElementById('time-chart');
    if (!ctx) return;
    
    // Create line chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Files Created/Modified',
                data: data.counts,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Files by Modification Time',
                    color: 'white',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Month',
                        color: 'white'
                    },
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Files',
                        color: 'white'
                    },
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// Utility function to generate chart colors
function generateChartColors(count) {
    // Predefined colors for common charts
    const predefinedColors = [
        'rgba(255, 99, 132, 0.7)',   // Red
        'rgba(54, 162, 235, 0.7)',   // Blue
        'rgba(255, 206, 86, 0.7)',   // Yellow
        'rgba(75, 192, 192, 0.7)',   // Green
        'rgba(153, 102, 255, 0.7)',  // Purple
        'rgba(255, 159, 64, 0.7)',   // Orange
        'rgba(199, 199, 199, 0.7)',  // Gray
        'rgba(83, 102, 255, 0.7)',   // Indigo
        'rgba(255, 99, 255, 0.7)',   // Pink
        'rgba(0, 202, 146, 0.7)'     // Teal
    ];
    
    // If we need more colors than predefined, generate random ones
    if (count <= predefinedColors.length) {
        return predefinedColors.slice(0, count);
    }
    
    // Generate additional random colors
    const colors = [...predefinedColors];
    
    for (let i = predefinedColors.length; i < count; i++) {
        const r = Math.floor(Math.random() * 255);
        const g = Math.floor(Math.random() * 255);
        const b = Math.floor(Math.random() * 255);
        colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
    }
    
    return colors;
}
