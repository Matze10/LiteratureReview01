```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif', 'lineWidth': '2px', 'primaryBorderColor': '#555', 'primaryColor': '#f0f0f0', 'primaryTextColor': '#333', 'secondaryColor': '#e0e0e0', 'secondaryTextColor': '#444', 'tertiaryColor': '#d0d0d0', 'tertiaryTextColor': '#555' }}}%%
graph TD

    %% Define styles
    classDef database fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,rx:8px
    classDef process fill:#BBDEFB,stroke:#2196F3,stroke-width:2px,rx:8px
    classDef review fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,rx:8px
    classDef analysis fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,rx:8px
    classDef storage fill:#D1C4E9,stroke:#673AB7,stroke-width:2px,rx:8px

    %% Data Sources
    subgraph Sources [Data Sources]
        direction TB
        Scopus[":mag_right: Scopus"]:::database
        WoS[":books: Web of Science"]:::database
    end

    %% Database Storage
    Database["SQLite Database"]:::storage

    %% Refinement Process
    Refinement["Refinement Engine\n(Scopus First, Then CrossRef)"]:::process
    Validation["Validation Module"]:::process
    CrossRef[":link: CrossRef"]:::database

    %% Processing Pipeline
    subgraph ProcessingPipeline [Processing System]
        direction TB
        DataLoader["Data Loader"]:::process
        DocProcessing["Document Processing"]:::process
        SaveToDB["Save Refined Data"]:::storage
    end

    %% Screening & Sorting
    subgraph ScreeningSorting [Screening & Sorting]
        ASReview["ASReview Sorting"]:::review
        SaveScreened["Store Sorted Papers"]:::storage
    end

    %% Analysis
    subgraph AnalysisVisualization [Analysis System]
        AnalysisR["Load Data into R\nfor Analysis & Visualization"]:::analysis
    end

    %% Workflow Connections
    Scopus --> Database
    WoS --> Database
    Database --> DataLoader
    DataLoader --> Refinement
    Refinement -->|Found| Validation
    Refinement -->|Not Found| CrossRef
    CrossRef --> Refinement
    Validation --> SaveToDB
    SaveToDB --> ASReview
    ASReview --> SaveScreened
    SaveScreened --> AnalysisR

