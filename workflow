%%{init: {  'theme': 'base',  'themeVariables': {    'fontSize': '16px',    'fontFamily': 'Helvetica Neue, Helvetica, Arial, sans-serif',    'lineWidth': '2px',    'primaryBorderColor': '#555',    'primaryColor': '#f0f0f0',    'primaryTextColor': '#333',    'secondaryColor': '#e0e0e0',    'secondaryTextColor': '#444',    'tertiaryColor': '#d0d0d0',    'tertiaryTextColor': '#555'  }}}%%
flowchart TB
    classDef database fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,rx:10px
    classDef process fill:#bbdefb,stroke:#2196f3,stroke-width:2px,rx:10px
    classDef review fill:#fff3e0,stroke:#ff9800,stroke-width:2px,rx:10px
    classDef analysis fill:#fce4ec,stroke:#e91e63,stroke-width:2px,rx:10px
    classDef api fill:#ede7f6,stroke:#673ab7,stroke-width:2px,rx:10px

    subgraph HalfCircle ["Data Pipeline"]
        direction LR

        subgraph Input ["<span style='font-size:20px; font-weight:bold;'>1️⃣ Data Collection</span>"]
            direction TB
            Scopus[":mag_right: Scopus"]:::database
            WoS[":books: Web of Science"]:::database
            Springer[":open_book: Springer"]:::database
        end

        subgraph Processing ["<span style='font-size:20px; font-weight:bold;'>2️⃣ Processing</span>"]
            direction TB
            Load["📥 Load & Parse"]:::process
            DB1["💾 Temp DB"]:::database
            subgraph Enrichment ["Enrichment"]
                direction LR
                API1["🌐 Scopus API"]:::api
                API2["🔗 CrossRef API"]:::api
                Valid["✅ Validate & Tag"]:::process
            end
            DB2["📚 Refined DB"]:::database
        end

        subgraph Review ["<span style='font-size:20px; font-weight:bold;'>3️⃣ Review</span>"]
            direction TB
            Sort["🤖 ASReview"]:::review
            Clean["✨ Final Set"]:::review
        end

        subgraph Analysis ["<span style='font-size:20px; font-weight:bold;'>4️⃣ Analysis</span>"]
            direction TB
            Conv["🐍→R Convert"]:::analysis
            Store["📊 RDS Store"]:::database
            R["📈 R Analysis"]:::analysis
        end

        Input --> Processing
        Processing --> Review
        Review --> Analysis
        Processing -- "Enrichment" --> Enrichment
        Load --> DB1
        DB1 --> API1
        API1 -->|Not Found| API2
        API1 & API2 -->|Success| Valid
        Valid --> DB2
        DB2 --> Sort
        Sort --> Clean
        Clean --> Conv
        Conv --> Store
        Store --> R

        style HalfCircle fill:#f8f8f8,stroke:#888,stroke-width:2px,rx:10px
    end
