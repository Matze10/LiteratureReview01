```mermaid
%%{init: {  'theme': 'base',  'themeVariables': {    'fontSize': '16px',    'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif',    'lineWidth': '2px',    'primaryBorderColor': '#555',    'primaryColor': '#f0f0f0',    'primaryTextColor': '#333',    'secondaryColor': '#e0e0e0',    'secondaryTextColor': '#444',    'tertiaryColor': '#d0d0d0',    'tertiaryTextColor': '#555'  }}}%%
flowchart LR
    subgraph Databases [Databases]
        direction LR
        ScopusDB[":mag_right: Scopus"]:::database
        CrossRefDB[":link: CrossRef"]:::database
    end

    DataLoader["DataLoader"]:::process --> DBSave1["DBSave"]:::database
    DBSave1 --> RefinementCall["Refinement call\nScopus / CrossRef"]:::process

    RefinementCall -->|NotFound| CrossRefDB
    RefinementCall -->|Success & Validate| SuccessValidate["Success & Validate"]:::process
    SuccessValidate --> DBSave2["DBSave"]:::database

    DBSave2 --> ASReview["ASReview\n<img src='https://asreview.ai/static/media/logo.924259ba.svg' width='50'/>"]:::review

    ASReview --> DBSave3["DBSave"]:::database
    DBSave3 --> AnalysisR["Analysis R"]:::analysis

    %% Styling
    classDef database fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,rx:10px
    classDef process fill:#bbdefb,stroke:#2196f3,stroke-width:2px,rx:10px
    classDef review fill:#fff3e0,stroke:#ff9800,stroke-width:2px,rx:10px
    classDef analysis fill:#fce4ec,stroke:#e91e63,stroke-width:2px,rx:10px

    style Databases fill:#f8f8f8,stroke:#888,stroke-width:2px,rx:10px
