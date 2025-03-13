
version 1.0

task run_phs2dd_script {
  input {
    File script
    String phs_id
  }

  command <<<
    # Option B approach: If we stick with a plain python:3 image, we must install gsutil:
    apt-get update
    apt-get install -y apt-transport-https ca-certificates gnupg
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
        | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    apt-get update
    apt-get install -y google-cloud-sdk

    # Debug info
    gsutil version
    pwd
    ls -al

    # Install Python libs
    pip install requests beautifulsoup4 lxml

    # Run the script
    python3 ~{script} -phs ~{phs_id}

    echo "After script run, listing CSVs:"
    ls -al *.csv || echo "No CSV found"

    # If you do want to copy them to the bucket right away, you can:
    # gsutil cp *.csv gs://fc-96e29e51-79cf-4213-a2ad-26f84a89aa25/

    # Either way, we capture them in the output block too.
    ls *.csv > csv_file_list.txt
  >>>

  runtime {
    docker: "python:3"
  }

  output {
    File log_file = "phs2dd.log"
    # This will capture any CSV in the working directory
    Array[File] csv_outputs = glob("*.csv")
    File csv_file_list = "csv_file_list.txt"
  }
}

workflow phs2dd_workflow {
  input {
    File myScript
    String myPhsId
  }

  call run_phs2dd_script {
    input:
      script = myScript,
      phs_id = myPhsId
  }

  output {
    File workflow_log = run_phs2dd_script.log_file
    Array[File] workflow_csvs = run_phs2dd_script.csv_outputs
    File csv_file_list = run_phs2dd_script.csv_file_list
  }
}

