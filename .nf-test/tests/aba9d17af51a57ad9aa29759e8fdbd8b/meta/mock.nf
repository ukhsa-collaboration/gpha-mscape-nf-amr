import groovy.json.JsonGenerator
import groovy.json.JsonGenerator.Converter

nextflow.enable.dsl=2

// comes from nf-test to store json files
params.nf_test_output  = ""

// include dependencies


// include test process
include { GZ_TO_FASTQ } from '/home/jovyan/git/gpha-mscape-nf-amr/modules/local/gunzip.nf'

// define custom rules for JSON that will be generated.
def jsonOutput =
    new JsonGenerator.Options()
        .addConverter(Path) { value -> value.toAbsolutePath().toString() } // Custom converter for Path. Only filename
        .build()

def jsonWorkflowOutput = new JsonGenerator.Options().excludeNulls().build()


workflow {

    // run dependencies
    

    // process mapping
    def input = []
    
                // define inputs of the process here. Example:
                input[0] = Channel.of(
                    tuple(
                        "climb-id",
                        file("/home/jovyan/git/gpha-mscape-nf-amr/tests/test_data/ERR3077524_GCF_013349085.1_1x.fq.gz")
                    )
                )
                
    //----

    //run process
    GZ_TO_FASTQ(*input)

    if (GZ_TO_FASTQ.output){

        // consumes all named output channels and stores items in a json file
        for (def name in GZ_TO_FASTQ.out.getNames()) {
            serializeChannel(name, GZ_TO_FASTQ.out.getProperty(name), jsonOutput)
        }	  
      
        // consumes all unnamed output channels and stores items in a json file
        def array = GZ_TO_FASTQ.out as Object[]
        for (def i = 0; i < array.length ; i++) {
            serializeChannel(i, array[i], jsonOutput)
        }    	

    }
  
}

def serializeChannel(name, channel, jsonOutput) {
    def _name = name
    def list = [ ]
    channel.subscribe(
        onNext: {
            list.add(it)
        },
        onComplete: {
              def map = new HashMap()
              map[_name] = list
              def filename = "${params.nf_test_output}/output_${_name}.json"
              new File(filename).text = jsonOutput.toJson(map)		  		
        } 
    )
}


workflow.onComplete {

    def result = [
        success: workflow.success,
        exitStatus: workflow.exitStatus,
        errorMessage: workflow.errorMessage,
        errorReport: workflow.errorReport
    ]
    new File("${params.nf_test_output}/workflow.json").text = jsonWorkflowOutput.toJson(result)
    
}
