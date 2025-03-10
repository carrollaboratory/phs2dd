version 1.0

task run_phs2dd_script {
  input {
    # The Python script file (phs2dd.py) to run.
    File script

    # The dbGaP PHS ID to scrape.
    String phs_id
  }

  command <<<
    # Install required Python libraries inside the Docker container.
    pip install requests beautifulsoup4 lxml

    # Run the script, passing the PHS ID as an argument.
    python3 ~{script} -phs ~{phs_id}
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
