import argparse
import pandas as pd
from matplotlib import pyplot as plt
from os import path, listdir, remove
from PIL import Image
import seaborn as sns


def covplot():
    args = parse_args()
    
    # load coverage data into pandas dataframe
    print("Loading BED coverage data...")
    column_names = ['chrom', 'start', 'stop', 'exon_info', 'coverage']
    cov_data = pd.read_csv(args.coverage_bedfile,
                            compression='gzip',
                            header=0,
                            sep='\t',
                            names=column_names)
    # split the 4th column of bed file into individual columns
    cov_data[['gene', 'tx', 'exon']] = cov_data['exon_info'].str.split(';', 3, expand=True)
    cov_data = cov_data.sort_values(by=['gene'], ascending=True)

    # get list of unique genes
    print("Listing unique genes for coverage calculation...")
    genes = list(cov_data['gene'].unique())

    # split coverage data in set of 60 genes
    cov_dfs = []
    chunk_size = 60
    gene_chunks = chunk_list(genes, chunk_size)
    for gene_list in gene_chunks:
        tmp_df = cov_data[cov_data['gene'].isin(gene_list)]
        cov_dfs.append([tmp_df, gene_list])
    
    # generate plots for each set of genes
    print("Generating intermediate plot files...")
    iteration = 0
    for cov_df in cov_dfs:
        iteration += 1
        generate_plot(cov_df, args.sample_name, args.output_path, args.output_format, iteration)
    print("Generate PDF plot file...")
    output_pdf_file = generate_pdf(args.output_path, args.sample_name)

    print(f"Plot saved at {output_pdf_file}")

def generate_pdf(output_path, sample_name):
    # find list of png files in the output folder
    png_files = [path.join(output_path, x) for x in listdir(output_path) if (x.endswith('.png') and sample_name in x)]
    png_files.sort()
    output_pdf_file = path.join(output_path, f'{sample_name}_gene_coverage_plot.pdf')
    output_pdf_hdl = Image.open(png_files[0]).convert('RGB')
    cov_images = []
    for image_file in png_files[1:]:
        cov_images.append(Image.open(image_file).convert('RGB'))
    output_pdf_hdl.save(output_pdf_file, save_all=True, append_images=cov_images)
    # delete the intermediate png files
    for image_file in png_files:
        remove(image_file)
    return output_pdf_file
    

def generate_plot(cov_df, sample_name, output_path, file_type, iteration):
    plt.figure(figsize=(30,17.14))
    plt.rcParams['axes.labelsize'] = 22
    plt.rcParams['xtick.labelsize'] = 16
    plt.rcParams['ytick.labelsize'] = 16
    ax = sns.barplot(x='gene', y='coverage', data=cov_df[0], ci=False)
    ax.set_xticklabels(labels = cov_df[1], rotation=90)
    ax.axhline(300)
    plt.xlabel('Gene')
    plt.ylabel('Coverage')
    plt.title(f'Per gene coverage - {sample_name}', fontsize=40, pad=30)
    plt.subplots_adjust(bottom=0.2)
    output_file = path.join(output_path, f"{sample_name}_gene_coverage_set{iteration}.{file_type}")
    plt.savefig(output_file, dpi=300)

def chunk_list(input_list, chunk_size):
    retinfo = []
    counter = 0
    tmp_list = []
    for item in input_list:
        counter += 1
        if counter > chunk_size:
            counter = 0
            retinfo.append(tmp_list)
            tmp_list = []
        tmp_list.append(item)
    if len(tmp_list) > 0:
        retinfo.append(tmp_list)
    return retinfo

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--coverage-bedfile",
                        type=check_path,
                        required=True,
                        help="CNR file containing weighted log2 ratio info.")
    parser.add_argument("-o", "--output-path",
                        type=check_path,
                        required=True,
                        help="Output folder to save plot images. This folder must exist.")
    parser.add_argument("-f", "--output-format",
                        type=acceptable_formats,
                        default="png",
                        required=True,
                        help="Output file format. Supported types: png, jpg, tiff, pdf, svg. Default is png.")
    parser.add_argument("-s", "--sample-name",
                        type=str,
                        default="sample",
                        required=True,
                        help="Sample name to include in the chart title")
    return parser.parse_args()


def acceptable_formats(format: str):
    formats = ['png', 'jpg', 'tiff', 'svg', 'pdf']
    if format in formats:
        return format
    else:
        raise argparse.argparse.ArgumentTypeError(f'{format} is not a acceptable file format. Allowed types: png, jpg, tiff, pdf, svg.')

def check_path(file_path: str):
    if not path.exists(file_path):
        raise argparse.ArgumentTypeError("Error: Provided output directory does not exist.")
    else:
        return file_path

if __name__ == '__main__':
    covplot()