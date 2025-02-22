```mermaid
%%{init: {  'theme': 'base',  'themeVariables': {    'fontSize': '16px',    'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif',    'lineWidth': '2px',    'primaryBorderColor': '#555',    'primaryColor': '#f0f0f0',    'primaryTextColor': '#333',    'secondaryColor': '#e0e0e0',    'secondaryTextColor': '#444',    'tertiaryColor': '#d0d0d0',    'tertiaryTextColor': '#555'  }}}%%
flowchart LR
    subgraph Databases [Databases]
        direction LR
        ScopusDB[":mag_right: Scopus DB"]:::database
        CrossRefDB[":link: CrossRef DB"]:::database
    end

    subgraph DataSources [Data Sources]
        direction TB
        Scopus[":mag_right: Scopus"]:::source
        WoS[":books: Web of Science"]:::source
        Springer[":open_book: Springer"]:::source
    end

    Load["📥 Load & Parse"]:::process
    DB1["💾 Temp DB"]:::database
    Valid["✅ Validate & Tag"]:::process
    DB2["📚 Refined DB"]:::database
    Sort["🤖 ASReview"]:::review
    Clean["✨ Final Set"]:::review
    Conv["🐍→R Convert"]:::analysis
    Store["📊 RDS Store"]:::database
    R["📈 R Analysis"]:::analysis

    %% Connections
    DataSources --> Load
    Load --> DB1
    DB1 -->|Request| ScopusDB
    DB1 -->|Request (Fallback)| CrossRefDB
    ScopusDB -->|Response| Valid
    CrossRefDB -->|Response| Valid
    Valid --> DB2
    DB2 --> Sort
    Sort --> Clean
    Clean --> Conv
    Conv --> Store
    Store --> R

    %% Styling
    classDef database fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,rx:10px
    classDef process fill:#bbdefb,stroke:#2196f3,stroke-width:2px,rx:10px
    classDef review fill:#fff3e0,stroke:#ff9800,stroke-width:2px,rx:10px
    classDef analysis fill:#fce4ec,stroke:#e91e63,stroke-width:2px,rx:10px
    classDef source fill:#ede7f6,stroke:#673ab7,stroke-width:2px,rx:10px

    style Databases fill:#f8f8f8,stroke:#888,stroke-width:2px,rx:10px
    style DataSources fill:#f8f8f8,stroke:#888,stroke-width:2px,rx:10px
