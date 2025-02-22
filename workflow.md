```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif', 'lineWidth': '2px', 'primaryBorderColor': '#555', 'primaryColor': '#f0f0f0', 'primaryTextColor': '#333', 'secondaryColor': '#e0e0e0', 'secondaryTextColor': '#444', 'tertiaryColor': '#d0d0d0', 'tertiaryTextColor': '#555' }}}%%
flowchart TD

    %% Define styles
    classDef database fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,rx:8px
    classDef process fill:#BBDEFB,stroke:#2196F3,stroke-width:2px,rx:8px
    classDef review fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,rx:8px
    classDef analysis fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,rx:8px

    %% Databases (Starting Point)
    subgraph DataSources [Databases]
        direction TB
        Scopus[":mag_right: Scopus"]:::database
        WoS[":books: Web of Science"]:::database
    end

    %% Initial Data Load
    DataLoader["Load Data into Database"]:::process

    %% Refinement Process
    Refinement["Refinement (Scopus First, CrossRef if Needed)"]:::process
    Validation["Validate Refinement"]:::process

    %% Processing & Storage
    subgraph ProcessingPipeline [Processing & Storage]
        direction TB
        SQLGen["SQLite DB Generator"]:::database
        DocProcessing["Document Processing"]:::process
        SaveToDB["Save Refined Data to DB"]:::database
    end

    %% Screening & Sorting
    subgraph ScreeningSorting [Screening & Sorting]
        ASReview["ASReview\n<img src='https://asreview.ai/static/media/logo.924259ba.svg' width='50'/>"]:::review
        SaveScreened["Save Sorted Papers to DB"]:::database
    end

    %% Analysis
    subgraph AnalysisVisualization [Analysis & Visualization]
        AnalysisR["Load Data into R for Analysis"]:::analysis
    end

    %% Workflow connections (L-Shaped)
    Scopus --> DataLoader
    WoS --> DataLoader
    DataLoader --> SQLGen
    SQLGen --> Refinement
    Refinement -->|Refined| Validation
    Validation --> SaveToDB
    SaveToDB --> ASReview
    ASReview --> SaveScreened
    SaveScreened --> AnalysisR


