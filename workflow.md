```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif', 'lineWidth': '2px', 'primaryBorderColor': '#555', 'primaryColor': '#f0f0f0', 'primaryTextColor': '#333', 'secondaryColor': '#e0e0e0', 'secondaryTextColor': '#444', 'tertiaryColor': '#d0d0d0', 'tertiaryTextColor': '#555' }}}%%
flowchart TD

    %% Define styles
    classDef database fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,rx:8px
    classDef process fill:#BBDEFB,stroke:#2196F3,stroke-width:2px,rx:8px
    classDef review fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,rx:8px
    classDef analysis fill:#FCE4EC,stroke:#E91E63,stroke-width:2px,rx:8px

    subgraph DataSources [Data Sources]
        direction LR
        Scopus[":mag_right: Scopus"]:::database
        CrossRef[":link: CrossRef"]:::database
    end

    subgraph ProcessingPipeline [Processing Pipeline]
        direction TB
        DataLoader["Data Loader\n(Extract Data)"]:::process
        SQLGen["SQLite DB Generator\n(Store in DB)"]:::database
        DocProcessing["Document Processing\n(Refinement & Cleaning)"]:::process
        SaveToDB["Save Refined Data to DB"]:::database
    end

    subgraph ScreeningSorting [Screening & Sorting]
        ASReview["ASReview\n<img src='https://asreview.ai/static/media/logo.924259ba.svg' width='50'/>"]:::review
        SaveScreened["Save Sorted Papers to DB"]:::database
    end

    subgraph AnalysisVisualization [Analysis & Visualization]
        AnalysisR["R Analysis\n(Generate Insights)"]:::analysis
    end

    %% Workflow connections
    Scopus --> DataLoader
    CrossRef --> DataLoader
    DataLoader --> SQLGen
    SQLGen --> DocProcessing
    DocProcessing --> SaveToDB
    SaveToDB --> ASReview
    ASReview --> SaveScreened
    SaveScreened --> AnalysisR

