version 1.0

task run_phs2dd_script {
  input {
    # The dbGaP PHS ID to scrape.
    String phs_id
  }


  command <<<
    pip install requests beautifulsoup4 lxml
    # Hardcode the download of the script via curl or wget, then run it:
    curl -L -o phs2dd.py https://raw.githubusercontent.com/mhigbyflowers/phs2dd/main/src/phs2dd.py
    python3 phs2dd.py -phs ~{phs_id}
  
  >>>

  runtime {
    # Use an official Python 3.9 Docker image so we have Python available.
    docker: "python:3.9"
  }

  output {
    # The script writes to a log file named 'phs2dd.log'.
    File log_file = "phs2dd.log"

    # The script generates one or more CSV files. 
    # We'll capture them all as an array of Files if they exist.
    Array[File] csv_outputs = glob("*.csv")
  }
}

workflow phs2dd_workflow {
  input {
    # The Python script file.
    File myScript

    # e.g. "phs000001"
    String myPhsId
  }

  call run_phs2dd_script {
    input:
      script = myScript,
      phs_id = myPhsId
  }

  output {
    # Expose the task outputs at the workflow level.
    File workflow_log = run_phs2dd_script.log_file
    Array[File] workflow_csvs = run_phs2dd_script.csv_outputs
  }
}
